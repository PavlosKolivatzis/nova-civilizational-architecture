"""
Checkpoint configuration for Autonomous Verification Ledger.

Phase 14-2: Merkle Checkpoints & PQC Signer
"""

import os
from dataclasses import dataclass


@dataclass
class CheckpointConfig:
    """Configuration for checkpoint operations."""

    # Enable checkpointing
    enabled: bool = bool(int(os.getenv("LEDGER_CHECKPOINT_ENABLED", "1")))

    # Minimum seconds between checkpoints
    every_seconds: int = int(os.getenv("LEDGER_CHECKPOINT_EVERY_SECONDS", "300"))

    # Minimum records required for checkpoint
    min_records: int = int(os.getenv("LEDGER_CHECKPOINT_MIN_RECORDS", "100"))