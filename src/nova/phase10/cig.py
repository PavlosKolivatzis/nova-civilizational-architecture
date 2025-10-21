"""Civilizational Intelligence Graph (CIG) — Phase 10.0.

Distributed knowledge synthesis across Nova deployments (stub implementation).
Full graph requires semantic embeddings (Phase 11+ scope).
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from datetime import datetime, timezone, timedelta
import hashlib


@dataclass
class KnowledgeNode:
    """Single knowledge node in CIG."""

    id: str
    source_deployment: str
    content_hash: str
    belief_ci: float = 0.95  # Confidence interval from Phase 6.0
    freshness_half_life_hours: int = 336  # 14 days default
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    metadata: Dict[str, Any] = field(default_factory=dict)

    def compute_freshness(self) -> float:
        """Compute temporal freshness score with exponential decay."""
        now = datetime.now(timezone.utc)
        node_time = datetime.fromisoformat(self.timestamp)
        hours_elapsed = (now - node_time).total_seconds() / 3600

        # Exponential decay: freshness = e^(-t / τ)
        import math
        decay_factor = math.exp(-hours_elapsed / self.freshness_half_life_hours)

        return round(decay_factor, 4)


class CivilizationalIntelligenceGraph:
    """CIG knowledge synthesis engine (stub)."""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize CIG with optional configuration."""
        self.config = config or {}
        self.freshness_threshold = self.config.get("freshness_threshold", 0.5)

        # Graph storage (simple dict for stub; production would use graph DB)
        self.nodes: Dict[str, KnowledgeNode] = {}
        self.edges: List[Dict[str, Any]] = []  # Placeholder for relationships

    def add_node(
        self,
        node_id: str,
        source_deployment: str,
        content: str,
        **metadata
    ) -> KnowledgeNode:
        """Add knowledge node to graph."""
        content_hash = hashlib.sha256(content.encode()).hexdigest()

        node = KnowledgeNode(
            id=node_id,
            source_deployment=source_deployment,
            content_hash=content_hash,
            metadata=metadata,
        )

        self.nodes[node_id] = node
        return node

    def get_node(self, node_id: str) -> Optional[KnowledgeNode]:
        """Retrieve knowledge node."""
        return self.nodes.get(node_id)

    def detect_contradictions(self) -> List[Dict[str, Any]]:
        """Detect contradictory knowledge (stub: hash-based detection)."""
        contradictions = []
        content_hashes: Dict[str, List[str]] = {}

        # Group nodes by content hash
        for node_id, node in self.nodes.items():
            if node.content_hash not in content_hashes:
                content_hashes[node.content_hash] = []
            content_hashes[node.content_hash].append(node_id)

        # Detect nodes with same hash from different deployments (potential conflict)
        for content_hash, node_ids in content_hashes.items():
            if len(node_ids) > 1:
                deployments = {self.nodes[nid].source_deployment for nid in node_ids}
                if len(deployments) > 1:
                    contradictions.append({
                        "content_hash": content_hash,
                        "node_ids": node_ids,
                        "deployments": list(deployments),
                        "reason": "multi_deployment_hash_collision",
                    })

        return contradictions

    def compute_cgc(self) -> float:
        """Compute Cognitive Graph Coherence.

        Stub formula: CGC = avg_freshness × (1 - contradiction_rate)
        """
        if not self.nodes:
            return 1.0  # Empty graph = perfect coherence

        # Average freshness
        freshness_scores = [node.compute_freshness() for node in self.nodes.values()]
        avg_freshness = sum(freshness_scores) / len(freshness_scores)

        # Contradiction rate
        contradictions = self.detect_contradictions()
        contradiction_rate = len(contradictions) / len(self.nodes)

        cgc = avg_freshness * (1.0 - contradiction_rate)

        return round(cgc, 4)

    def prune_stale_nodes(self) -> int:
        """Remove nodes below freshness threshold."""
        pruned = 0
        stale_ids = []

        for node_id, node in self.nodes.items():
            if node.compute_freshness() < self.freshness_threshold:
                stale_ids.append(node_id)

        for node_id in stale_ids:
            del self.nodes[node_id]
            pruned += 1

        return pruned

    def get_metrics(self) -> Dict[str, Any]:
        """Export CIG operational metrics."""
        cgc = self.compute_cgc()

        return {
            "cgc": cgc,
            "total_nodes": len(self.nodes),
            "contradictions_detected": len(self.detect_contradictions()),
            "avg_freshness": round(
                sum(n.compute_freshness() for n in self.nodes.values()) / len(self.nodes), 3
            ) if self.nodes else 1.0,
        }
