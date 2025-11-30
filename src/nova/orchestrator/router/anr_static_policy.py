from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Any

from nova.orchestrator.router.decision import PolicyResult


@dataclass
class StaticPolicyConfig:
    """Configurable coefficients for deterministic routing."""

    base_score: float = 0.6
    risk_penalty: float = 0.4
    novelty_bonus: float = 0.2
    urgency_bonus: float = 0.15
    safe_mode_threshold: float = 0.35
    low_trust_threshold: float = 0.5


class StaticPolicyEngine:
    """A deterministic policy that mirrors ANR outputs without online learning."""

    def __init__(self, config: StaticPolicyConfig | None = None):
        self.config = config or StaticPolicyConfig()

    def evaluate(self, features: Dict[str, Any]) -> PolicyResult:
        risk = float(features.get("risk", 0.5))
        novelty = float(features.get("novelty", 0.3))
        urgency = float(features.get("urgency", 0.2))

        score = (
            self.config.base_score
            - (risk * self.config.risk_penalty)
            + (novelty * self.config.novelty_bonus)
            + (urgency * self.config.urgency_bonus)
        )

        if score < self.config.safe_mode_threshold:
            route = "safe_mode"
        elif score < self.config.low_trust_threshold:
            route = "low_trust"
        else:
            route = "primary"

        score = max(0.0, min(1.0, score))
        details = {"risk": risk, "novelty": novelty, "urgency": urgency}
        return PolicyResult(route=route, score=score, details=details)
