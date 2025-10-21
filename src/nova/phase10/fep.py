"""Federated Ethical Protocol (FEP) — Phase 10.0.

Multi-deployment ethical consensus with cryptographic voting and provenance chains.
"""

import hashlib
import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from datetime import datetime, timezone


@dataclass
class Vote:
    """Single node vote in FEP consensus."""

    node_id: str
    weight: float
    alignment: float  # 0.0-1.0: agreement with proposal
    provenance_integrity: float = 1.0
    signature: str = ""
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def __post_init__(self):
        """Generate signature if not provided."""
        if not self.signature:
            payload = f"{self.node_id}:{self.alignment}:{self.timestamp}"
            self.signature = hashlib.sha256(payload.encode()).hexdigest()[:16]


@dataclass
class FEPDecision:
    """Federated ethical decision with consensus metadata."""

    id: str
    topic: str
    votes: List[Vote]
    threshold: float = 0.90
    fcq: float = 0.0
    dissent_notes: List[str] = field(default_factory=list)
    decay_recheck_after_hours: int = 72
    provenance: Optional[Dict[str, Any]] = None
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def __post_init__(self):
        """Compute FCQ and provenance if not provided."""
        if self.fcq == 0.0:
            self.fcq = self.compute_fcq()
        if self.provenance is None:
            self.provenance = self._build_provenance()

    def compute_fcq(self) -> float:
        """Compute Federated Consensus Quality.

        Formula: FCQ = Σ(weight × alignment × provenance_integrity) / total_weight
        """
        if not self.votes:
            return 0.0

        numerator = sum(
            v.weight * v.alignment * v.provenance_integrity
            for v in self.votes
        )
        denominator = sum(v.weight for v in self.votes)

        return round(numerator / denominator, 3) if denominator > 0 else 0.0

    def _build_provenance(self) -> Dict[str, Any]:
        """Build cryptographic provenance chain."""
        import json

        vote_data = [
            {
                "node_id": v.node_id,
                "alignment": v.alignment,
                "signature": v.signature,
            }
            for v in self.votes
        ]

        payload = json.dumps(vote_data, sort_keys=True).encode()
        decision_hash = hashlib.sha256(payload).hexdigest()

        return {
            "hash": decision_hash,
            "parent_hash": "phase9-fehs-baseline",  # Link to Phase 9.0
            "timestamp": self.timestamp,
        }

    def is_approved(self) -> bool:
        """Check if decision meets consensus threshold."""
        return self.fcq >= self.threshold

    def record_dissent(self, node_id: str, reason: str):
        """Record dissenting opinion (preserved for audit)."""
        dissent_msg = f"{node_id}: {reason}"
        if dissent_msg not in self.dissent_notes:
            self.dissent_notes.append(dissent_msg)

    def to_dict(self) -> Dict[str, Any]:
        """Export decision as dictionary."""
        return {
            "id": self.id,
            "topic": self.topic,
            "threshold": self.threshold,
            "fcq": self.fcq,
            "votes": [
                {
                    "node_id": v.node_id,
                    "weight": v.weight,
                    "alignment": v.alignment,
                    "provenance_integrity": v.provenance_integrity,
                    "signature": v.signature,
                }
                for v in self.votes
            ],
            "dissent_notes": self.dissent_notes,
            "decay_recheck_after_hours": self.decay_recheck_after_hours,
            "provenance": self.provenance,
            "timestamp": self.timestamp,
        }


class FederatedEthicalProtocol:
    """FEP consensus engine for multi-deployment ethical decisions."""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize FEP with optional configuration."""
        self.config = config or {}
        self.threshold = self.config.get("fcq_threshold", 0.90)
        self.decay_hours = self.config.get("decay_hours", 72)
        self.record_dissent = self.config.get("record_dissent", True)

        # Storage
        self.decisions: Dict[str, FEPDecision] = {}
        self.pending_proposals: Dict[str, Dict[str, Any]] = {}

    def submit_proposal(
        self,
        decision_id: str,
        topic: str,
        **kwargs
    ) -> Dict[str, Any]:
        """Submit ethical decision proposal for federated voting."""
        if decision_id in self.decisions:
            return {"error": "decision_id already exists"}

        self.pending_proposals[decision_id] = {
            "topic": topic,
            "votes": [],
            "threshold": kwargs.get("threshold", self.threshold),
            "created_at": datetime.now(timezone.utc).isoformat(),
        }

        return {"status": "proposal_submitted", "decision_id": decision_id}

    def vote(
        self,
        decision_id: str,
        node_id: str,
        alignment: float,
        weight: float = 1.0,
        dissent_reason: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Cast vote on pending proposal."""
        if decision_id not in self.pending_proposals:
            return {"error": "proposal not found"}

        proposal = self.pending_proposals[decision_id]

        # Create vote
        vote = Vote(
            node_id=node_id,
            weight=weight,
            alignment=max(0.0, min(1.0, alignment)),  # Clamp to [0, 1]
        )

        proposal["votes"].append(vote)

        # Record dissent if provided
        if dissent_reason and self.record_dissent:
            if "dissent_notes" not in proposal:
                proposal["dissent_notes"] = []
            proposal["dissent_notes"].append(f"{node_id}: {dissent_reason}")

        return {
            "status": "vote_recorded",
            "decision_id": decision_id,
            "node_id": node_id,
            "votes_count": len(proposal["votes"]),
        }

    def finalize(self, decision_id: str) -> FEPDecision:
        """Finalize decision after voting completes."""
        if decision_id not in self.pending_proposals:
            raise ValueError(f"Proposal {decision_id} not found")

        proposal = self.pending_proposals.pop(decision_id)

        decision = FEPDecision(
            id=decision_id,
            topic=proposal["topic"],
            votes=proposal["votes"],
            threshold=proposal["threshold"],
            dissent_notes=proposal.get("dissent_notes", []),
            decay_recheck_after_hours=self.decay_hours,
        )

        self.decisions[decision_id] = decision
        return decision

    def get_decision(self, decision_id: str) -> Optional[FEPDecision]:
        """Retrieve finalized decision."""
        return self.decisions.get(decision_id)

    def get_metrics(self) -> Dict[str, Any]:
        """Export FEP operational metrics."""
        approved = sum(1 for d in self.decisions.values() if d.is_approved())
        total = len(self.decisions)

        avg_fcq = (
            sum(d.fcq for d in self.decisions.values()) / total
            if total > 0
            else 0.0
        )

        return {
            "total_decisions": total,
            "approved_decisions": approved,
            "pending_proposals": len(self.pending_proposals),
            "average_fcq": round(avg_fcq, 3),
            "threshold": self.threshold,
        }
