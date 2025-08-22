from __future__ import annotations

from typing import Dict, Any, Tuple

from slot06_cultural_synthesis.multicultural_truth_synthesis import (
    CulturalProfile,
    GuardrailValidationResult,
    DeploymentGuardrailResult,
)

from .models import MLSDecision


class MetaLegitimacySeal:
    """Final non-overridable cultural check integrating Slot-6 guardrails."""

    def __init__(self, slot6_adapter) -> None:  # slot6 adapter provides validate()
        self._slot6 = slot6_adapter

    def assess(
        self, profile: CulturalProfile, institution_type: str, payload: Dict[str, Any]
    ) -> Tuple[MLSDecision, GuardrailValidationResult]:
        """Evaluate guardrails and return final MLS decision."""
        res = self._slot6.validate(profile, institution_type, payload)
        decision = MLSDecision.QUARANTINE
        if res.result == DeploymentGuardrailResult.APPROVED:
            decision = MLSDecision.ALLOW
        elif res.result == DeploymentGuardrailResult.REQUIRES_TRANSFORMATION:
            decision = MLSDecision.ALLOW_TRANSFORMED
        return decision, res
