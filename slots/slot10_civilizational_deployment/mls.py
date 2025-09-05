from __future__ import annotations

import json
from typing import Dict, Any, Tuple

from slots.slot06_cultural_synthesis.multicultural_truth_synthesis import (
    CulturalProfile,
    GuardrailValidationResult,
)
from frameworks.enums import DeploymentGuardrailResult
from .models import MLSDecision


class MetaLegitimacySeal:
    """Final non-overridable cultural check integrating Slot-6 guardrails."""

    def __init__(self, slot6_adapter, slot2: Any | None = None) -> None:
        self._slot6 = slot6_adapter
        self._slot2 = slot2

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

    def _screen_with_slot2(self, plan_snapshot: Dict[str, Any]) -> Dict[str, Any]:
        """Screen deployment plan through Slot 2 ΔTHRESH with version handling."""
        if not self._slot2:
            return {"threat_level": 0.0, "patterns_detected": []}
        try:
            content = json.dumps(plan_snapshot, sort_keys=True)
            result = self._slot2.process_content(content, "deployment_verification")
            from slots.slot02_deltathresh.adapters import adapt_processing_result
            result = adapt_processing_result(result)
            version = getattr(result, "version", "v1")
            if version != "v1":
                raise ValueError(f"Unsupported ProcessingResult version: {version}")
            layer_scores = getattr(result, "layer_scores", {}) or {}
            tri_score = float(getattr(result, "tri_score", 1.0))
            tri_min = float(
                getattr(
                    getattr(self._slot2, "config", type("C", (), {"tri_min_score": 0.8})),
                    "tri_min_score",
                    0.8,
                )
            )
            risk = max(layer_scores.values()) if layer_scores else 0.0
            tri_gap = max(0.0, tri_min - tri_score)
            threat_level = getattr(result, "threat_level", None)
            if threat_level is None:
                threat_level = min(1.0, 0.5 * risk + 0.5 * tri_gap)
            return {
                "threat_level": float(threat_level),
                "patterns_detected": list(getattr(result, "patterns_detected", []))
                or list(layer_scores.keys()),
            }
        except Exception:
            return {"threat_level": 0.0, "patterns_detected": []}
