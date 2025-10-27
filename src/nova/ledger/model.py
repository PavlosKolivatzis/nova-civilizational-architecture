"""
Ledger data models for Autonomous Verification Ledger (AVL).

Phase 13: Immutable, hash-linked records for cross-slot trust provenance.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Dict, Any, Optional


class RecordKind(str, Enum):
    """Types of ledger records."""

    # Slot01: Truth Anchor events
    ANCHOR_CREATED = "ANCHOR_CREATED"
    PQC_SIGNED = "PQC_SIGNED"

    # Slot02: Delta Threshold events
    DELTATHRESH_APPLIED = "DELTATHRESH_APPLIED"
    FIDELITY_BROADCAST = "FIDELITY_BROADCAST"

    # Slot08: Memory Lock / Verification events
    PQC_VERIFIED = "PQC_VERIFIED"
    PQC_KEY_ROTATED = "PQC_KEY_ROTATED"

    # Generic
    CHECKPOINT_CREATED = "CHECKPOINT_CREATED"


@dataclass
class LedgerRecord:
    """
    Immutable ledger record with hash-linked continuity.

    Each record references the previous record's hash for the same anchor_id,
    forming a tamper-evident chain.
    """

    # Identity
    rid: str  # UUIDv7 for time-ordered identifiers
    anchor_id: str  # Truth anchor this record pertains to

    # Metadata
    slot: str  # Slot ID (e.g., "01", "02", "08")
    kind: RecordKind  # Event type
    ts: datetime  # Timestamp (UTC)

    # Chain integrity
    prev_hash: Optional[str]  # SHA3-256 of previous record for this anchor_id
    hash: str  # SHA3-256 of this record's canonical representation

    # Content
    payload: Dict[str, Any]  # Canonical JSON with event-specific data
    sig: Optional[bytes] = None  # Optional PQC signature

    # Provenance
    producer: str = "unknown"  # Service/slot that created this record
    version: str = "unknown"  # Software version

    def __post_init__(self):
        """Validate record invariants."""
        if not self.rid:
            raise ValueError("rid is required")
        if not self.anchor_id:
            raise ValueError("anchor_id is required")
        if not self.hash:
            raise ValueError("hash is required")


@dataclass
class Checkpoint:
    """
    Signed Merkle root checkpoint for batch verification.

    Periodically created to certify integrity of a range of records.
    """

    cid: str  # Checkpoint UUID
    range_start: str  # First record ID in range
    range_end: str  # Last record ID in range
    merkle_root: str  # SHA3-256 Merkle root of record hashes
    sig: Optional[bytes] = None  # PQC signature over checkpoint
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    record_count: int = 0  # Number of records in checkpoint range


@dataclass
class TrustScore:
    """
    Computed trust score for an anchor based on ledger evidence.

    Aggregates fidelity, PQC verification, and continuity signals.
    """

    anchor_id: str
    overall: float  # [0, 1] composite score
    fidelity_mean: float  # Average quantum fidelity
    pqc_rate: float  # Fraction of records with valid PQC signatures
    verify_rate: float  # Fraction of verifications that passed
    continuity_ok: bool  # Hash chain is intact
    chain_length: int  # Number of records in anchor's chain
    computed_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
