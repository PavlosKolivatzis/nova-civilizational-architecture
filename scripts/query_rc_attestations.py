#!/usr/bin/env python3
"""
Query RC Attestation History

Retrieves and displays RC validation attestation records from Phase 14 ledger.

Usage:
    python scripts/query_rc_attestations.py --phase 7.0-rc
    python scripts/query_rc_attestations.py --phase 7.0-rc --summary
    python scripts/query_rc_attestations.py --phase 7.0-rc --verify
    python scripts/query_rc_attestations.py --hash <attestation_hash>
"""

import argparse
import json
import sys
from pathlib import Path

# Add src to path
repo_root = Path(__file__).parent.parent
sys.path.insert(0, str(repo_root / "src"))

from nova.ledger.rc_query import (
    get_rc_chain,
    get_rc_attestation_by_hash,
    verify_rc_chain,
    get_rc_summary,
)


def format_record(record) -> str:
    """Format a ledger record for display."""
    payload = record.payload
    rc_criteria = payload.get("rc_criteria", {})

    status = "PASS" if rc_criteria.get("overall_pass") else "FAIL"
    memory = payload.get("memory_resonance", {}).get("stability", 0.0)
    ris = payload.get("ris", {}).get("score", 0.0)
    stress = payload.get("stress_resilience", {}).get("recovery_rate", 0.0)

    lines = [
        f"Record ID: {record.rid}",
        f"Timestamp: {record.ts.isoformat()}",
        f"Status: {status}",
        f"Attestation Hash: {payload.get('attestation_hash', 'N/A')[:16]}...",
        f"Memory Stability: {memory:.3f}",
        f"RIS Score: {ris:.3f}",
        f"Stress Recovery: {stress:.3f}",
        f"Signature: {len(record.sig)}b" if record.sig else "Signature: None",
        f"Hash: {record.hash[:16]}...",
        f"Prev Hash: {record.prev_hash[:16] if record.prev_hash else 'None'}...",
    ]
    return "\n".join(lines)


def cmd_list(args):
    """List all RC attestations for a phase."""
    chain = get_rc_chain(args.phase)

    if not chain:
        print(f"No RC attestations found for phase {args.phase}")
        return 1

    print(f"RC Attestation Chain: {args.phase}")
    print(f"Total Records: {len(chain)}")
    print("=" * 70)

    for i, record in enumerate(chain):
        print(f"\n[{i+1}/{len(chain)}]")
        print(format_record(record))

    return 0


def cmd_summary(args):
    """Show summary statistics for RC attestations."""
    summary = get_rc_summary(args.phase)

    print(f"RC Attestation Summary: {args.phase}")
    print("=" * 70)
    print(f"Total Attestations: {summary['count']}")
    print(f"Chain Valid: {'OK' if summary['chain_valid'] else 'FAIL'}")

    if summary['errors']:
        print(f"Errors: {len(summary['errors'])}")
        for error in summary['errors'][:5]:
            print(f"  - {error}")

    if summary['count'] > 0:
        print(f"\nFirst Attestation: {summary['first_attestation']}")
        print(f"Last Attestation: {summary['last_attestation']}")
        print(f"\nPass Rate: {summary['pass_rate']*100:.1f}% ({summary['pass_count']}/{summary['count']})")
        print(f"\nAverage Metrics:")
        print(f"  Memory Stability: {summary['avg_memory_stability']:.3f}")
        print(f"  RIS Score: {summary['avg_ris_score']:.3f}")
        print(f"  Stress Recovery: {summary['avg_stress_recovery']:.3f}")

    return 0


def cmd_verify(args):
    """Verify RC attestation chain integrity."""
    is_valid, errors = verify_rc_chain(args.phase)

    print(f"RC Attestation Chain Verification: {args.phase}")
    print("=" * 70)

    if is_valid:
        print("[OK] Chain is valid")
        chain = get_rc_chain(args.phase)
        print(f"  {len(chain)} records verified")
        print(f"  Hash chain continuity: OK")
        print(f"  All signatures present: {'YES' if all(r.sig for r in chain) else 'NO'}")
        return 0
    else:
        print("[FAIL] Chain validation failed")
        print(f"\nErrors ({len(errors)}):")
        for error in errors:
            print(f"  - {error}")
        return 1


def cmd_get_by_hash(args):
    """Get specific attestation by hash."""
    record = get_rc_attestation_by_hash(args.hash, args.phase)

    if not record:
        print(f"No attestation found with hash {args.hash[:16]}...")
        return 1

    print(f"RC Attestation: {args.hash[:16]}...")
    print("=" * 70)
    print(format_record(record))

    if args.json:
        print("\nFull JSON Payload:")
        print(json.dumps(record.payload, indent=2))

    return 0


def main():
    parser = argparse.ArgumentParser(
        description="Query RC attestation history from Phase 14 ledger",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    parser.add_argument(
        "--phase",
        default="7.0-rc",
        help="RC phase identifier (default: 7.0-rc)"
    )
    parser.add_argument(
        "--summary",
        action="store_true",
        help="Show summary statistics"
    )
    parser.add_argument(
        "--verify",
        action="store_true",
        help="Verify chain integrity"
    )
    parser.add_argument(
        "--hash",
        help="Get attestation by attestation_hash"
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Include full JSON payload (with --hash)"
    )

    args = parser.parse_args()

    try:
        if args.hash:
            return cmd_get_by_hash(args)
        elif args.summary:
            return cmd_summary(args)
        elif args.verify:
            return cmd_verify(args)
        else:
            return cmd_list(args)

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
