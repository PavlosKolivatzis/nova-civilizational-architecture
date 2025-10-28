"""
PQC-signed Merkle checkpoints for ledger integrity.

Phase 14-2: Merkle Checkpoints & PQC Signer
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from .merkle import merkle_root
from .store_postgres import PostgresLedgerStore


@dataclass
class Checkpoint:
    """
    Signed Merkle checkpoint over a range of ledger records.

    Provides tamper-evident batch verification of ledger integrity.
    """
    cid: str
    merkle_root_hex: str
    range_start: str  # ISO timestamp
    range_end: str    # ISO timestamp
    records: int
    algo: str = "sha3-256"
    version: str = "cp-1.0"
    sig_b64: str = ""
    pubkey_id: str = ""
    created_at: Optional[datetime] = None

    def to_header(self) -> dict:
        """Convert to canonical header for signing."""
        return {
            "merkle_root_hex": self.merkle_root_hex,
            "range_start": self.range_start,
            "range_end": self.range_end,
            "records": self.records,
            "algo": self.algo,
            "version": self.version
        }


class CheckpointSigner:
    """
    Builds and signs Merkle checkpoints using Dilithium2 PQC.

    Reuses PQC infrastructure from Phase 12C.
    """

    def __init__(self, store: PostgresLedgerStore):
        self.store = store
        # Lazy import to avoid circular dependencies
        self._keyring = None

    @property
    def keyring(self):
        """Lazy-loaded PQC keyring."""
        if self._keyring is None:
            # Import here to avoid circular dependency
            from nova.crypto.pqc_keyring import Dilithium2Keyring
            self._keyring = Dilithium2Keyring()
        return self._keyring

    async def build_and_sign(self, start_ts: str, end_ts: str) -> Checkpoint:
        """
        Build Merkle root from records in time range and sign it.

        Args:
            start_ts: ISO timestamp for range start
            end_ts: ISO timestamp for range end

        Returns:
            Signed Checkpoint
        """
        # Query record hashes in the time range
        hashes_hex = await self.store.query_hashes_between(start_ts, end_ts)
        if not hashes_hex:
            raise ValueError(f"No records found in range {start_ts} to {end_ts}")

        # Convert to bytes and compute Merkle root
        digests = [bytes.fromhex(h) for h in hashes_hex]
        root = merkle_root(digests)

        # Create checkpoint
        import uuid
        cid = str(uuid.uuid4())

        checkpoint = Checkpoint(
            cid=cid,
            merkle_root_hex=root.hex(),
            range_start=start_ts,
            range_end=end_ts,
            records=len(digests)
        )

        # Sign the canonical header
        header = checkpoint.to_header()
        msg = self._canonical_header(header)
        sig_b64, pubkey_id = self.keyring.sign_b64(msg)

        checkpoint.sig_b64 = sig_b64
        checkpoint.pubkey_id = pubkey_id

        # Persist to database
        await self.store.insert_checkpoint(checkpoint)

        return checkpoint

    def verify(self, checkpoint: Checkpoint) -> bool:
        """
        Verify checkpoint signature and Merkle root.

        Args:
            checkpoint: Checkpoint to verify

        Returns:
            True if signature and root are valid
        """
        header = checkpoint.to_header()
        msg = self._canonical_header(header)
        return self.keyring.verify_b64(msg, checkpoint.sig_b64, checkpoint.pubkey_id)

    async def verify_range(self, checkpoint: Checkpoint) -> tuple[bool, str]:
        """
        Verify checkpoint signature and recompute Merkle root.

        Args:
            checkpoint: Checkpoint to verify

        Returns:
            (is_valid, error_message)
        """
        # First verify signature
        if not self.verify(checkpoint):
            return False, "Invalid signature"

        # Recompute Merkle root
        try:
            hashes_hex = await self.store.query_hashes_between(
                checkpoint.range_start, checkpoint.range_end
            )
            digests = [bytes.fromhex(h) for h in hashes_hex]
            computed_root = merkle_root(digests)

            if computed_root.hex() != checkpoint.merkle_root_hex:
                return False, f"Merkle root mismatch: expected {checkpoint.merkle_root_hex}, got {computed_root.hex()}"

            if len(digests) != checkpoint.records:
                return False, f"Record count mismatch: expected {checkpoint.records}, got {len(digests)}"

            return True, ""

        except Exception as e:
            return False, f"Verification error: {e}"

    @staticmethod
    def _canonical_header(header: dict) -> bytes:
        """
        Create canonical byte representation for signing.

        Uses sorted JSON with compact separators for deterministic output.
        """
        return json.dumps(header, sort_keys=True, separators=(",", ":")).encode("utf-8")