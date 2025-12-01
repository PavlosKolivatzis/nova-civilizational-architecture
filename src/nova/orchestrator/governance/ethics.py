from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Any, List


@dataclass
class EthicsCheck:
    rule: str
    passed: bool
    weight: float
    explanation: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "rule": self.rule,
            "passed": self.passed,
            "weight": self.weight,
            "explanation": self.explanation,
        }


def evaluate_ethics(state: Dict[str, Any]) -> List[EthicsCheck]:
    """Evaluate Nova CE-00* ethics invariants."""
    checks: List[EthicsCheck] = []
    consent_profile = str(state.get("consent_profile", "CE001_standard"))
    ce001_pass = consent_profile == "CE001_standard"
    checks.append(
        EthicsCheck(
            rule="CE-001",
            passed=ce001_pass,
            weight=0.35,
            explanation="Consent profile must be CE001_standard.",
        )
    )

    disclosure = str(state.get("disclosure", "full")).lower()
    ce002_pass = disclosure == "full"
    checks.append(
        EthicsCheck(
            rule="CE-002",
            passed=ce002_pass,
            weight=0.20,
            explanation="Declarative transparency requires disclosure='full'.",
        )
    )

    honesty = state.get("relational_honesty", True)
    ce005_pass = bool(honesty)
    checks.append(
        EthicsCheck(
            rule="CE-005",
            passed=ce005_pass,
            weight=0.25,
            explanation="Relational honesty must be asserted by upstream slots.",
        )
    )

    dominance_factor = float(state.get("dominance_factor", 0.0) or 0.0)
    ce006_pass = dominance_factor <= 0.5
    checks.append(
        EthicsCheck(
            rule="CE-006",
            passed=ce006_pass,
            weight=0.20,
            explanation="Non-dominance requires dominance_factor <= 0.5.",
        )
    )

    return checks
