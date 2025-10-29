"""
Checkpoint service for creating and verifying Merkle checkpoints.

Phase 14-2: Merkle Checkpoints & PQC Signer
"""

import asyncio
import time
from typing import Optional

from .checkpoint_signer import CheckpointSigner
from .checkpoint_types import Checkpoint
from .store import LedgerStore
from .metrics import ledger_checkpoints_total, ledger_checkpoint_verify_failures_total


class CheckpointService:
    """
    Service for creating and verifying Merkle checkpoints.

    Provides high-level operations for checkpoint management.
    """

    def __init__(self, store: LedgerStore, signer: CheckpointSigner):
        """
        Initialize checkpoint service.

        Args:
            store: Ledger store instance
            signer: Checkpoint signer instance
        """
        self.store = store
        self.signer = signer

    async def create_and_sign(self, anchor_id: str) -> Checkpoint:
        """
        Create and sign a checkpoint for an anchor.

        Args:
            anchor_id: Anchor to create checkpoint for

        Returns:
            Signed Checkpoint
        """
        # Get span information for the anchor
        span = await self.store.span_for_checkpoint(anchor_id)
        if not span:
            raise ValueError(f"No records found for anchor {anchor_id}")

        # Sign the checkpoint
        checkpoint = await self.signer.sign_checkpoint(
            anchor_id=anchor_id,
            start_rid=span["start_rid"],
            end_rid=span["end_rid"],
            merkle_root=span["merkle_root"],
            prev_root=span.get("prev_root")
        )

        # Persist the checkpoint
        await self.store.persist_checkpoint(checkpoint)

        # Update metrics
        ledger_checkpoints_total.inc()

        return checkpoint

    async def verify(self, checkpoint_id: str) -> bool:
        """
        Verify a checkpoint by ID.

        Args:
            checkpoint_id: Checkpoint ID to verify

        Returns:
            True if checkpoint is valid
        """
        checkpoint = await self.store.fetch_checkpoint(checkpoint_id)
        if not checkpoint:
            return False

        is_valid, _ = await self.signer.verify_range(checkpoint)
        if not is_valid:
            ledger_checkpoint_verify_failures_total.inc()

        return is_valid