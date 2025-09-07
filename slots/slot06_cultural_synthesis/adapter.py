from __future__ import annotations

from typing import Any, Dict, Optional

from frameworks.enums import DeploymentGuardrailResult
from slots.slot02_deltathresh.models import ProcessingResult

from .engine import (
    AdaptiveSynthesisEngine,
    CulturalProfile,
    GuardrailValidationResult,
    SimulationResult,
)


class MulticulturalTruthSynthesisAdapter:
    def __init__(self, engine: AdaptiveSynthesisEngine):
        self.engine = engine

    def analyze_cultural_context(
        self,
        institution_name: str,
        ctx: Optional[Dict[str, Any]] = None,
        slot2_result: ProcessingResult | Dict[str, Any] | None = None,
    ) -> CulturalProfile:
        try:
            res = self.engine.analyze_and_simulate(
                institution_name, {"content": ""}, ctx or {}, slot2_result=slot2_result
            )
            return res.cultural_profile
        except Exception:
            return CulturalProfile()

    def validate_cultural_deployment(
        self,
        profile: CulturalProfile,
        institution_type: str,
        payload: Dict[str, Any],
        slot2_result: ProcessingResult | Dict[str, Any] | None = None,
    ) -> GuardrailValidationResult:
        try:
            res = self.engine.analyze_and_simulate(
                institution_type, payload, {}, profile, slot2_result=slot2_result
            )
            status_map = {
                SimulationResult.APPROVED: DeploymentGuardrailResult.APPROVED,
                SimulationResult.APPROVED_WITH_TRANSFORMATION: DeploymentGuardrailResult.REQUIRES_TRANSFORMATION,
                SimulationResult.BLOCKED_BY_GUARDRAIL: DeploymentGuardrailResult.BLOCKED_PRINCIPLE_VIOLATION,
                SimulationResult.DEFERRED_NO_CONSENT: DeploymentGuardrailResult.BLOCKED_CULTURAL_SENSITIVITY,
            }
            return GuardrailValidationResult(
                result=status_map.get(res.simulation_status, DeploymentGuardrailResult.ERROR),
                compliance_score=res.compliance_score,
                violations=res.violations,
                recommendations=res.recommendations,
                transformation_required=(res.simulation_status == SimulationResult.APPROVED_WITH_TRANSFORMATION),
                max_safe_adaptation=AdaptiveSynthesisEngine._max_safe_adaptation(profile),
                tri_gap=res.cultural_profile.tri_gap,
                slot2_patterns=res.cultural_profile.slot2_patterns,
            )
        except Exception:
            return GuardrailValidationResult(
                result=DeploymentGuardrailResult.ERROR,
                compliance_score=0.0,
                violations=["Validation process failed"],
                recommendations=["Check system logs"],
                transformation_required=False,
                max_safe_adaptation=AdaptiveSynthesisEngine._max_safe_adaptation(profile),
                tri_gap=0.0,
                slot2_patterns=[],
            )
