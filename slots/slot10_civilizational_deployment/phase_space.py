from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Any

from .models import ThreatLevel


@dataclass
class NovaPhaseSpaceSimulator:
    """Lightweight topology snapshot of deployed nodes."""

    nodes: Dict[str, Dict[str, Any]] = field(default_factory=dict)

    def register(self, name: str, profile: Any, threat: ThreatLevel = ThreatLevel.LOW) -> None:
        self.nodes[name] = {"profile": profile, "threat": threat}

    def snapshot(self) -> Dict[str, Any]:
        return {"count": len(self.nodes), "nodes": list(self.nodes.keys())}
