#!/usr/bin/env python3
"""
Ledger checkpoint CLI tool.

Phase 14-2: Merkle Checkpoints & PQC Signer
"""

import argparse
import asyncio
import json
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from nova.ledger.factory import create_ledger_store
from nova.ledger.checkpoint_service import CheckpointService


def setup_logging(verbose: bool = False):
    """Setup logging configuration."""
    import logging
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )


async def roll_checkpoint(start_ts: str = None, end_ts: str = None):
    """Roll a new checkpoint."""
    store = create_ledger_store()
    service = CheckpointService(store)

    try:
        checkpoint = await service.roll_once(start_ts=start_ts, end_ts=end_ts)

        print("✅ Checkpoint created successfully!")
        print(f"   CID: {checkpoint.cid}")
        print(f"   Root: {checkpoint.merkle_root_hex}")
        print(f"   Range: {checkpoint.range_start} → {checkpoint.range_end}")
        print(f"   Records: {checkpoint.records}")
        print(f"   Signature: {checkpoint.sig_b64[:32]}...")
        print(f"   PubKey ID: {checkpoint.pubkey_id}")

        return checkpoint

    except Exception as e:
        print(f"❌ Failed to create checkpoint: {e}")
        sys.exit(1)


async def get_latest_checkpoint():
    """Get the latest checkpoint."""
    store = create_ledger_store()

    try:
        checkpoint = await store.get_latest_checkpoint()
        if not checkpoint:
            print("❌ No checkpoints found")
            sys.exit(1)

        print("📋 Latest Checkpoint:")
        print(f"   CID: {checkpoint.cid}")
        print(f"   Root: {checkpoint.merkle_root}")
        print(f"   Range: {checkpoint.range_start} → {checkpoint.range_end}")
        print(f"   Records: {checkpoint.record_count}")
        if checkpoint.sig:
            print(f"   Signature: {checkpoint.sig.hex()[:32]}...")
        if checkpoint.created_at:
            print(f"   Created: {checkpoint.created_at.isoformat()}")

        return checkpoint

    except Exception as e:
        print(f"❌ Failed to get latest checkpoint: {e}")
        sys.exit(1)


async def get_checkpoint(cid: str):
    """Get checkpoint by ID."""
    store = create_ledger_store()

    try:
        checkpoint = await store.get_checkpoint(cid)
        if not checkpoint:
            print(f"❌ Checkpoint {cid} not found")
            sys.exit(1)

        print(f"📋 Checkpoint {cid}:")
        print(f"   Root: {checkpoint.merkle_root}")
        print(f"   Range: {checkpoint.range_start} → {checkpoint.range_end}")
        print(f"   Records: {checkpoint.record_count}")
        if checkpoint.sig:
            print(f"   Signature: {checkpoint.sig.hex()[:32]}...")
        if checkpoint.created_at:
            print(f"   Created: {checkpoint.created_at.isoformat()}")

        return checkpoint

    except Exception as e:
        print(f"❌ Failed to get checkpoint {cid}: {e}")
        sys.exit(1)


async def verify_checkpoint(cid: str):
    """Verify checkpoint signature and Merkle root."""
    store = create_ledger_store()
    service = CheckpointService(store)

    try:
        checkpoint = await store.get_checkpoint(cid)
        if not checkpoint:
            print(f"❌ Checkpoint {cid} not found")
            sys.exit(1)

        # Convert to new format for verification
        from nova.ledger.checkpoint_signer import Checkpoint
        cp = Checkpoint(
            cid=checkpoint.cid,
            merkle_root_hex=checkpoint.merkle_root,
            range_start=checkpoint.range_start,
            range_end=checkpoint.range_end,
            records=checkpoint.record_count,
            sig_b64=checkpoint.sig.hex() if checkpoint.sig else "",
            pubkey_id="",  # Legacy checkpoints don't have pubkey_id
            created_at=checkpoint.created_at
        )

        is_valid, error = await service.signer.verify_range(cp)

        if is_valid:
            print(f"✅ Checkpoint {cid} verification PASSED")
            print(f"   Root: {cp.merkle_root_hex}")
            print(f"   Records: {cp.records}")
        else:
            print(f"❌ Checkpoint {cid} verification FAILED: {error}")
            sys.exit(1)

        return is_valid

    except Exception as e:
        print(f"❌ Failed to verify checkpoint {cid}: {e}")
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(
        description="Ledger checkpoint management tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Roll a checkpoint for last hour
  python scripts/ledger_checkpoint.py roll --start "2025-10-28T10:00:00Z" --end "2025-10-28T11:00:00Z"

  # Roll checkpoint with defaults (last checkpoint end → now)
  python scripts/ledger_checkpoint.py roll

  # Get latest checkpoint
  python scripts/ledger_checkpoint.py latest

  # Get specific checkpoint
  python scripts/ledger_checkpoint.py get abc123-def456

  # Verify checkpoint
  python scripts/ledger_checkpoint.py verify abc123-def456
        """
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Roll command
    roll_parser = subparsers.add_parser("roll", help="Create a new checkpoint")
    roll_parser.add_argument("--start", help="Start timestamp (ISO format)")
    roll_parser.add_argument("--end", help="End timestamp (ISO format, default: now)")

    # Latest command
    subparsers.add_parser("latest", help="Get the latest checkpoint")

    # Get command
    get_parser = subparsers.add_parser("get", help="Get checkpoint by ID")
    get_parser.add_argument("cid", help="Checkpoint ID")

    # Verify command
    verify_parser = subparsers.add_parser("verify", help="Verify checkpoint signature and root")
    verify_parser.add_argument("cid", help="Checkpoint ID to verify")

    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Enable verbose logging"
    )

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    setup_logging(args.verbose)

    if args.command == "roll":
        asyncio.run(roll_checkpoint(args.start, args.end))
    elif args.command == "latest":
        asyncio.run(get_latest_checkpoint())
    elif args.command == "get":
        asyncio.run(get_checkpoint(args.cid))
    elif args.command == "verify":
        asyncio.run(verify_checkpoint(args.cid))


if __name__ == "__main__":
    main()
