from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class ConstraintResult:
    allowed: bool
    reasons: List[str] = field(default_factory=list)
    snapshot: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "allowed": self.allowed,
            "reasons": list(self.reasons),
            "snapshot": dict(self.snapshot),
        }


@dataclass
class PolicyResult:
    route: str
    score: float
    details: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "route": self.route,
            "score": self.score,
            "details": dict(self.details),
        }


@dataclass
class AdvisorScore:
    name: str
    score: float
    details: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "score": self.score,
            "details": dict(self.details),
        }


@dataclass
class RouterDecision:
    route: str
    constraints: ConstraintResult
    policy: PolicyResult
    advisors: Dict[str, AdvisorScore] = field(default_factory=dict)
    final_score: float = 0.0
    metadata: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        advisors_dict = {name: advisor.to_dict() for name, advisor in self.advisors.items()}
        return {
            "route": self.route,
            "constraints": self.constraints.to_dict(),
            "policy": self.policy.to_dict(),
            "advisors": advisors_dict,
            "final_score": self.final_score,
            "metadata": dict(self.metadata or {}),
        }
