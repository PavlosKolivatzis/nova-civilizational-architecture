"""Provenance & Consensus Registry (PCR) — Phase 10.0.

Immutable append-only ledger for federated decisions with Merkle-tree structure.
"""

import hashlib
import json
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from datetime import datetime, timezone


@dataclass
class LedgerEntry:
    """Single entry in the PCR ledger."""

    entry_id: str
    decision_id: str
    decision_hash: str
    parent_hash: str
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    merkle_root: str = ""

    def __post_init__(self):
        """Compute Merkle root if not provided."""
        if not self.merkle_root:
            self.merkle_root = self._compute_merkle_root()

    def _compute_merkle_root(self) -> str:
        """Compute Merkle root for this entry."""
        payload = f"{self.entry_id}:{self.decision_hash}:{self.parent_hash}:{self.timestamp}"
        return hashlib.sha256(payload.encode()).hexdigest()

    def verify(self) -> bool:
        """Verify entry integrity (recompute Merkle root)."""
        expected = self._compute_merkle_root()
        return self.merkle_root == expected


class ProvenanceConsensusRegistry:
    """PCR ledger for immutable federated decision tracking."""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize PCR with optional configuration."""
        self.config = config or {}
        self.verify_interval_seconds = self.config.get("verify_interval_seconds", 600)

        # Ledger storage (append-only)
        self.ledger: List[LedgerEntry] = []
        self.index: Dict[str, int] = {}  # decision_id -> ledger position

        # Metrics
        self.verification_count = 0
        self.broken_chain_count = 0

    def append(
        self,
        decision_id: str,
        decision_hash: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> LedgerEntry:
        """Append decision to ledger (immutable operation)."""
        if decision_id in self.index:
            raise ValueError(f"Decision {decision_id} already in ledger")

        # Parent hash is previous entry's Merkle root (or genesis)
        parent_hash = (
            self.ledger[-1].merkle_root
            if self.ledger
            else "phase9-nci-baseline"  # Link to Phase 9.0
        )

        entry_id = f"pcr-{len(self.ledger):06d}"
        entry = LedgerEntry(
            entry_id=entry_id,
            decision_id=decision_id,
            decision_hash=decision_hash,
            parent_hash=parent_hash,
        )

        self.ledger.append(entry)
        self.index[decision_id] = len(self.ledger) - 1

        return entry

    def get_entry(self, decision_id: str) -> Optional[LedgerEntry]:
        """Retrieve ledger entry by decision ID."""
        if decision_id not in self.index:
            return None
        return self.ledger[self.index[decision_id]]

    def verify_chain(self, start_index: int = 0) -> Dict[str, Any]:
        """Verify Merkle chain integrity from start_index to end."""
        self.verification_count += 1

        if not self.ledger:
            return {"pis": 1.0, "verified": True, "breaks": [], "entries_checked": 0}

        breaks = []

        for i in range(start_index, len(self.ledger)):
            entry = self.ledger[i]

            # Verify entry internal integrity
            if not entry.verify():
                breaks.append(
                    {
                        "index": i,
                        "entry_id": entry.entry_id,
                        "reason": "merkle_root_mismatch",
                    }
                )

            # Verify chain linkage (except first entry)
            if i > 0:
                prev_entry = self.ledger[i - 1]
                if entry.parent_hash != prev_entry.merkle_root:
                    breaks.append(
                        {
                            "index": i,
                            "entry_id": entry.entry_id,
                            "reason": "parent_hash_mismatch",
                            "expected": prev_entry.merkle_root,
                            "actual": entry.parent_hash,
                        }
                    )

        if breaks:
            self.broken_chain_count += 1

        # Compute PIS (Provenance Integrity Score)
        total_entries = len(self.ledger) - start_index
        broken_entries = len(breaks)
        pis = (total_entries - broken_entries) / total_entries if total_entries > 0 else 1.0

        return {
            "pis": round(pis, 4),
            "verified": len(breaks) == 0,
            "breaks": breaks,
            "entries_checked": total_entries,
        }

    def regenerate(self, break_index: int) -> Dict[str, Any]:
        """Regenerate chain from break_index (autonomous repair)."""
        if break_index >= len(self.ledger):
            return {"error": "invalid_index"}

        # Recompute Merkle roots and parent hashes from break_index onward
        repaired = 0

        for i in range(break_index, len(self.ledger)):
            entry = self.ledger[i]

            # Fix parent hash
            if i > 0:
                prev_entry = self.ledger[i - 1]
                entry.parent_hash = prev_entry.merkle_root

            # Recompute Merkle root
            entry.merkle_root = entry._compute_merkle_root()
            repaired += 1

        return {
            "status": "regenerated",
            "repaired_entries": repaired,
            "start_index": break_index,
        }

    def export_audit_trail(self, format: str = "json-ld") -> str:
        """Export ledger for audit (JSON-LD linked data)."""
        if format != "json-ld":
            raise ValueError(f"Unsupported format: {format}")

        audit_data = {
            "@context": "https://nova.civilizational.arch/phase10/pcr",
            "@type": "ProvenanceLedger",
            "entries": [
                {
                    "@id": entry.entry_id,
                    "decision_id": entry.decision_id,
                    "decision_hash": entry.decision_hash,
                    "parent_hash": entry.parent_hash,
                    "merkle_root": entry.merkle_root,
                    "timestamp": entry.timestamp,
                }
                for entry in self.ledger
            ],
            "total_entries": len(self.ledger),
            "verification_count": self.verification_count,
        }

        return json.dumps(audit_data, indent=2)

    def get_metrics(self) -> Dict[str, Any]:
        """Export PCR operational metrics."""
        verification_result = self.verify_chain()

        return {
            "total_entries": len(self.ledger),
            "pis": verification_result["pis"],
            "chain_verified": verification_result["verified"],
            "verification_count": self.verification_count,
            "broken_chain_count": self.broken_chain_count,
            "breaks_detected": len(verification_result["breaks"]),
        }
