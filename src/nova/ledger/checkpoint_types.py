"""
Checkpoint domain model for Phase 14-2.

Phase 14-2: Merkle Checkpoints & PQC Signer
"""

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional


@dataclass(frozen=True)
class Checkpoint:
    """
    Signed Merkle checkpoint over a range of ledger records.

    Provides tamper-evident batch verification of ledger integrity.
    """
    id: str                    # uuid4 checkpoint ID
    anchor_id: str             # uuid4 anchor this checkpoint covers
    merkle_root: str           # hex sha3-256 Merkle root
    start_rid: str             # uuid of first record included
    end_rid: str               # uuid of last record included
    prev_root: Optional[str]   # previous checkpoint's root for chaining
    ts: str = ""               # ISO timestamp when created
    sig: Optional[bytes] = None      # PQC signature bytes
    key_id: Optional[str] = None     # PQC key identifier
    version: str = "cp-v1"     # checkpoint format version

    def __post_init__(self):
        """Set timestamp if not provided."""
        if not self.ts:
            object.__setattr__(self, 'ts', datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "id": self.id,
            "anchor_id": self.anchor_id,
            "merkle_root": self.merkle_root,
            "start_rid": self.start_rid,
            "end_rid": self.end_rid,
            "prev_root": self.prev_root,
            "ts": self.ts,
            "sig": self.sig.hex() if self.sig else None,
            "key_id": self.key_id,
            "version": self.version
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Checkpoint":
        """Create from dictionary."""
        sig = bytes.fromhex(data["sig"]) if data.get("sig") else None
        return cls(
            id=data["id"],
            anchor_id=data["anchor_id"],
            merkle_root=data["merkle_root"],
            start_rid=data["start_rid"],
            end_rid=data["end_rid"],
            prev_root=data.get("prev_root"),
            ts=data["ts"],
            sig=sig,
            key_id=data.get("key_id"),
            version=data.get("version", "cp-v1")
        )