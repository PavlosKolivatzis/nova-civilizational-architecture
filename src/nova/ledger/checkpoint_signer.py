"""
PQC-signed Merkle checkpoints for ledger integrity.

Phase 14-2: Merkle Checkpoints & PQC Signer
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

import base64
from .store_postgres import PostgresLedgerStore
from .checkpoint_types import Checkpoint


def _decode_sig(sig_str: str) -> bytes:
    """
    Accept either base64 (preferred) or 0x-prefixed hex for backward compat.
    """
    s = sig_str.strip()
    if s.startswith("0x"):  # legacy hex path
        return bytes.fromhex(s[2:])
    # tolerate missing base64 padding
    pad = '=' * (-len(s) % 4)
    return base64.b64decode(s + pad)


# Checkpoint class moved to checkpoint_types.py


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
            from nova.crypto.pqc_keyring import PQCKeyring
            self._keyring = PQCKeyring()
        return self._keyring

    async def sign_checkpoint(self, anchor_id: str, start_rid: str, end_rid: str, merkle_root: str, prev_root: Optional[str] = None) -> Checkpoint:
        """
        Sign a checkpoint with the given parameters.

        Args:
            anchor_id: Anchor this checkpoint covers
            start_rid: First record ID in range
            end_rid: Last record ID in range
            merkle_root: Hex Merkle root
            prev_root: Previous checkpoint root for chaining

        Returns:
            Signed Checkpoint
        """
        import uuid
        cid = str(uuid.uuid4())

        checkpoint = Checkpoint(
            id=cid,
            anchor_id=anchor_id,
            merkle_root=merkle_root,
            start_rid=start_rid,
            end_rid=end_rid,
            prev_root=prev_root
        )

        # Sign the canonical representation
        msg = self._canonical_bytes(checkpoint)
        sig_b64, pubkey_id = self.keyring.sign_b64(msg)

        # Create signed checkpoint
        signed_checkpoint = Checkpoint(
            id=cid,
            anchor_id=anchor_id,
            merkle_root=merkle_root,
            start_rid=start_rid,
            end_rid=end_rid,
            prev_root=prev_root,
            sig=_decode_sig(sig_b64),  # base64 → bytes
            key_id=pubkey_id
        )

        return signed_checkpoint

    def verify_checkpoint(self, checkpoint: Checkpoint) -> bool:
        """
        Verify checkpoint signature.

        Args:
            checkpoint: Checkpoint to verify

        Returns:
            True if signature is valid
        """
        if not checkpoint.sig or not checkpoint.key_id:
            return False

        msg = self._canonical_bytes(checkpoint)
        # Convert sig back to base64 for keyring.verify_b64
        if isinstance(checkpoint.sig, bytes):
            sig_b64 = base64.b64encode(checkpoint.sig).decode('utf-8')
        else:
            sig_b64 = checkpoint.sig
        ok = self.keyring.verify_b64(msg, sig_b64, checkpoint.key_id)
        return bool(ok)

    async def build_and_sign(self, store, anchor_id: str, start_rid: str, end_rid: str):
        """Build and sign a checkpoint."""
        hashes = await store.query_hashes_between_rids(start_rid, end_rid)
        if not hashes:
            return None
        from .merkle import merkle_root_from_hashes
        root = merkle_root_from_hashes(hashes)
        return await self.sign_checkpoint(anchor_id, start_rid, end_rid, root)

    async def verify_range(self, store, anchor_id: str, start_rid: str, end_rid: str, merkle_root: str) -> tuple[bool, Optional[str]]:
        """
        Verify a checkpoint's Merkle range.

        Args:
            store: Ledger store
            anchor_id: Anchor ID
            start_rid: Start record ID
            end_rid: End record ID
            merkle_root: Expected Merkle root

        Returns:
            (is_valid, error_message)
        """
        hashes = await store.query_hashes_between_rids(start_rid, end_rid)
        from .merkle import merkle_root_from_hashes
        calc = merkle_root_from_hashes(hashes)
        if calc != merkle_root:
            return False, "Merkle root mismatch"  # exact text expected by tests
        return True, None

    @staticmethod
    def _canonical_bytes(checkpoint: Checkpoint) -> bytes:
        """
        Create canonical byte representation for signing.

        Uses sorted JSON with compact separators for deterministic output.
        """
        # Create canonical representation excluding signature fields
        canonical_data = {
            "id": checkpoint.id,
            "anchor_id": checkpoint.anchor_id,
            "merkle_root": checkpoint.merkle_root,
            "start_rid": checkpoint.start_rid,
            "end_rid": checkpoint.end_rid,
            "prev_root": checkpoint.prev_root,
            "ts": checkpoint.ts,
            "version": checkpoint.version
        }
        return json.dumps(canonical_data, sort_keys=True, separators=(",", ":")).encode("utf-8")
