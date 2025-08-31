from __future__ import annotations

import hashlib
import secrets
from dataclasses import dataclass


@dataclass
class RealityLock:
    """Simple data lock with integrity verification."""

    anchor: str
    integrity_hash: str

    @classmethod
    def from_anchor(cls, anchor: str) -> "RealityLock":
        """Create a lock computing the integrity hash for ``anchor``."""
        digest = hashlib.sha256(anchor.encode()).hexdigest()
        return cls(anchor=anchor, integrity_hash=digest)

    def verify_integrity(self) -> bool:
        """Verify the integrity hash matches the current anchor."""
        expected_hash = hashlib.sha256(self.anchor.encode()).hexdigest()
        return secrets.compare_digest(self.integrity_hash, expected_hash)


# Backwards compatibility alias
Lock = RealityLock
