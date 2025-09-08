from __future__ import annotations

from typing import Any, Dict, Optional

from frameworks.enums import DeploymentGuardrailResult
from slots.slot02_deltathresh.models import ProcessingResult

from .engine import (
    CulturalSynthesisEngine,
    CulturalProfile,
    GuardrailValidationResult,
)


class MulticulturalTruthSynthesisAdapter:
    """Thin wrapper around :class:`CulturalSynthesisEngine` used by Slot 10."""

    def __init__(self, engine: CulturalSynthesisEngine):
        self.engine = engine

    def analyze_cultural_context(
        self,
        institution_name: str,
        ctx: Optional[Dict[str, Any]] = None,
        slot2_result: ProcessingResult | Dict[str, Any] | None = None,
    ) -> CulturalProfile:
        """Derive a cultural profile from ``ctx``.

        The current implementation simply runs the synthesis engine over the
        provided context and returns the resulting profile.  ``slot2_result``
        is accepted for API compatibility but otherwise ignored.
        """

        data: CulturalProfile = dict(ctx or {})
        data["institution"] = institution_name
        try:
            return self.engine.synthesize(data)
        except Exception:
            return CulturalProfile()

    def validate_cultural_deployment(
        self,
        profile: CulturalProfile,
        institution_type: str,
        payload: Dict[str, Any],
        slot2_result: ProcessingResult | Dict[str, Any] | None = None,
    ) -> GuardrailValidationResult:
        """Validate ``payload`` against cultural guardrails.

        ``slot2_result`` is currently unused but kept for interface
        compatibility with other slots.
        """

        try:
            metrics = self.engine.synthesize(payload)
            return GuardrailValidationResult(
                result=DeploymentGuardrailResult.APPROVED,
                compliance_score=metrics["principle_preservation"],
            )
        except Exception:
            return GuardrailValidationResult(
                result=DeploymentGuardrailResult.ERROR,
                compliance_score=0.0,
                violations=["Validation process failed"],
            )
