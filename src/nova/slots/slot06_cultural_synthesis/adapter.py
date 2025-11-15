from __future__ import annotations

from typing import Any, Dict, List, Optional
import warnings

from frameworks.enums import DeploymentGuardrailResult
from nova.slots.slot02_deltathresh.models import ProcessingResult

from .engine import CulturalSynthesisEngine, CulturalProfile, GuardrailValidationResult


RISK_BLOCK = 0.70  # residual_risk ≥ -> BLOCKED
RISK_TRANSFORM = 0.40  # residual_risk ≥ -> REQUIRES_TRANSFORMATION
PPS_MIN = 0.40  # if principle_preservation_score < -> escalate
PPS_BLOCK = 0.30


def _coalesce_slot2(slot2_result: Any) -> Dict[str, Any]:
    """Accept dict or object; extract what synthesize needs."""
    if slot2_result is None:
        return {
            "tri_score": 0.5,
            "layer_scores": {},
            "forbidden_hits": [],
            "tri_gap": 0.0,
            "slot2_patterns": [],
        }
    def get_value(key: str, default: Any = None) -> Any:
        if isinstance(slot2_result, dict):
            return slot2_result.get(key, default)
        return getattr(slot2_result, key, default)

    return {
        "tri_score": get_value("tri_score", 0.5),
        "layer_scores": get_value("layer_scores", {}) or {},
        "forbidden_hits": get_value("forbidden_hits", get_value("forbidden", [])) or [],
        "tri_gap": get_value("tri_gap", 0.0),
        "slot2_patterns": get_value("slot2_patterns", []),
    }


def _profile_consent(profile: Dict[str, Any]) -> bool:
    # be liberal in reading consent flags
    for k in ("consent_ok", "consent", "has_consent"):
        if k in profile:
            return bool(profile[k])
    return True  # default to True; engine will still sanity-check


class CulturalSynthesisAdapter:
    """Thin wrapper around :class:`CulturalSynthesisEngine` used by Slot 10."""

    def __init__(self, engine: CulturalSynthesisEngine):
        self.engine = engine

    def analyze_cultural_context(
        self,
        institution_name: str,
        ctx: Optional[Dict[str, Any]] = None,
        slot2_result: ProcessingResult | Dict[str, Any] | None = None,
    ) -> CulturalProfile:
        """Derive a cultural profile from ``ctx``."""

        data: CulturalProfile = dict(ctx or {})
        data["institution"] = institution_name
        try:
            result = self.engine.synthesize(data)
            # Ensure institution is included in response
            result["institution"] = institution_name
            return result
        except Exception:
            profile = CulturalProfile()
            profile["institution"] = institution_name
            return profile

    def validate_cultural_deployment(
        self,
        profile: CulturalProfile,
        institution_type: str,
        payload: Any,
        slot2_result: ProcessingResult | Dict[str, Any] | None = None,
        *,
        stability_index: Optional[float] = None,
    ) -> GuardrailValidationResult:
        """Validate ``payload`` against cultural guardrails."""

        if slot2_result is None:
            warnings.warn(
                "Slot6: validate_cultural_deployment called without slot2_result; "
                "falling back to neutral risk. Provide Slot 2 outputs to enforce guardrails.",
                RuntimeWarning,
                stacklevel=2,
            )

        s2 = _coalesce_slot2(slot2_result)
        consent_ok = _profile_consent(profile)

        content = payload.get("content") if isinstance(payload, dict) else str(payload)

        metrics = self.engine.synthesize(
            content,
            tri_score=float(s2["tri_score"]),
            layer_scores=dict(s2["layer_scores"]),
            forbidden_hits=list(s2["forbidden_hits"]),
            consent_ok=bool(consent_ok),
            stability_index=stability_index,
        )

        pps = float(
            metrics.get(
                "principle_preservation_score",
                metrics.get("principle_preservation", 0.0),
            )
        )
        # Clamp to valid bounds (safety measure)
        pps = max(0.0, min(1.0, pps))
        residual = float(metrics.get("residual_risk", 1.0))
        actions: List[str] = list(metrics.get("policy_actions", []))
        forbidden_hits: List[str] = list(
            metrics.get("forbidden_hits", s2["forbidden_hits"])
        )
        consent_required = bool(
            metrics.get("consent_required", not consent_ok)
        )

        if consent_required or not consent_ok:
            result = DeploymentGuardrailResult.BLOCKED_CULTURAL_SENSITIVITY
            violations = ["consent_required"]
        elif forbidden_hits and (residual >= RISK_BLOCK or pps < PPS_BLOCK):
            result = DeploymentGuardrailResult.BLOCKED_PRINCIPLE_VIOLATION
            violations = ["forbidden_content"]
        elif residual >= RISK_BLOCK or pps < PPS_BLOCK:
            result = DeploymentGuardrailResult.BLOCKED_PRINCIPLE_VIOLATION
            violations = [
                "high_residual_risk" if residual >= RISK_BLOCK else "low_principle_preservation"
            ]
        elif (
            forbidden_hits
            or residual >= RISK_TRANSFORM
            or pps < PPS_MIN
            or "rephrase:high-risk" in actions
        ):
            result = DeploymentGuardrailResult.REQUIRES_TRANSFORMATION
            violations = (
                (["forbidden_content"] if forbidden_hits else [])
                + (["elevated_residual_risk"] if residual >= RISK_TRANSFORM else [])
                + (["principle_preservation_weak"] if pps < PPS_MIN else [])
            )
        else:
            result = DeploymentGuardrailResult.APPROVED
            violations = []

        # Record decision metrics
        try:
            from orchestrator.metrics import get_slot6_metrics
            metrics_collector = get_slot6_metrics()
            metrics_collector.record_decision(
                result_name=result.name if hasattr(result, 'name') else str(result),
                pps=pps,
                residual_risk=residual,
                institution_type=institution_type,
                tri_score=s2["tri_score"],
                violations=len(violations)
            )
        except ImportError:
            # Metrics collection is optional
            pass

        return GuardrailValidationResult(
            result=result,
            compliance_score=pps,
            violations=violations,
            recommendations=actions,
            transformation_required=(
                result == DeploymentGuardrailResult.REQUIRES_TRANSFORMATION
            ),
            max_safe_adaptation=getattr(self.engine, "max_safe_adaptation", lambda *_: 1.0)(
                profile
            ),
            tri_gap=s2["tri_gap"],
            slot2_patterns=s2["slot2_patterns"],
        )


# Backwards compatibility alias
MulticulturalTruthSynthesisAdapter = CulturalSynthesisAdapter


__all__ = [
    "CulturalSynthesisAdapter",
    "MulticulturalTruthSynthesisAdapter",
    "DeploymentGuardrailResult",
    "GuardrailValidationResult",
]
