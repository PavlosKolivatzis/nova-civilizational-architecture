"""Simplified cultural synthesis engine for Slot 6.

This module exposes a small stateless engine focused on deriving three
core metrics from a cultural profile:

* ``adaptation_effectiveness`` – ability to adapt reasoning methods.
* ``principle_preservation`` – estimated retention of core principles.
* ``residual_risk`` – remaining deployment risk after adaptation.

The formulas were migrated from the previous adaptive synthesis engine
and are clamped to the ``[0.0, 1.0]`` interval.
"""

from __future__ import annotations

from dataclasses import dataclass, field, asdict, is_dataclass
from typing import Any, Dict, Mapping, Optional, TypedDict

from frameworks.enums import DeploymentGuardrailResult


class CulturalProfile(TypedDict, total=False):
    """Inputs for cultural synthesis.

    Only a handful of fields are required for the synthesis formulas, but
    the ``TypedDict`` remains extensible for future expansion.
    """

    clarity: float
    foresight: float
    empiricism: float
    anchor_confidence: float
    tri_score: float
    layer_scores: Mapping[str, float]
    ideology_push: bool


def slot2_threat_bridge(result: Any, tri_min_score: float = 0.8) -> float:
    """Compute threat level from a Slot 2 ProcessingResult.

    The function accepts either the modern dataclass representation or legacy
    mappings and normalises them via the Slot 2 adapter.  The threat level is
    derived from the maximum layer score and the TRI gap, matching the formula
    used in the legacy engine.
    """

    from nova.slots.slot02_deltathresh.adapters import adapt_processing_result

    if isinstance(result, dict) or not hasattr(result, "version"):
        if not isinstance(result, dict) and is_dataclass(result):
            result = adapt_processing_result(asdict(result))
        else:
            result = adapt_processing_result(result)

    layer_scores = getattr(result, "layer_scores", {}) or {}
    tri_score = float(getattr(result, "tri_score", 1.0))
    risk = max(layer_scores.values()) if layer_scores else 0.0
    tri_gap = max(0.0, tri_min_score - tri_score)
    threat_level = getattr(result, "threat_level", None)
    if threat_level is None:
        threat_level = min(1.0, 0.5 * risk + 0.5 * tri_gap)
    return float(threat_level)


@dataclass
class SynthesisConfig:
    """Configuration values used by :class:`CulturalSynthesisEngine`."""

    methods: Mapping[str, float] = field(
        default_factory=lambda: {
            "greek_logic": 0.8,
            "buddhist_impermanence": 0.7,
            "confucian_precision": 0.7,
            "indigenous_longterm": 0.8,
            "scientific_empiricism": 0.9,
        }
    )
    ideology_penalty: float = 0.05
    tri_min_score: float = 0.8


@dataclass
class GuardrailValidationResult:
    """Light-weight guardrail result used by higher level modules."""

    result: DeploymentGuardrailResult = DeploymentGuardrailResult.APPROVED
    compliance_score: float = 1.0
    violations: list[str] = field(default_factory=list)
    recommendations: list[str] = field(default_factory=list)
    transformation_required: bool = False
    max_safe_adaptation: float = 0.0
    tri_gap: float = 0.0
    slot2_patterns: list[str] = field(default_factory=list)
    tri_band: Optional[str] = None
    anchor_id: Optional[str] = None
    tri_signal: Dict[str, Any] = field(default_factory=dict)


class CulturalSynthesisEngine:
    """Compute cultural synthesis metrics.

    The engine performs no I/O and maintains no internal state beyond its
    configuration.  Each call to :meth:`synthesize` returns a dictionary
    with the three core metrics.
    """

    def __init__(self, config: SynthesisConfig | None = None) -> None:
        self.config = config or SynthesisConfig()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def synthesize(
        self,
        profile: CulturalProfile | str | Mapping[str, Any] | None = None,
        **overrides: Any,
    ) -> Dict[str, Any]:
        """Return synthesis metrics for ``profile`` or ``content``.

        The method accepts a flexible mapping or content string plus keyword
        overrides.  Unknown values are ignored, allowing callers to pass
        additional context without affecting the core formulas.
        """

        data: Dict[str, Any]
        if profile is None:
            data = {}
        elif isinstance(profile, Mapping):
            data = dict(profile)
        else:
            data = {"content": str(profile)}

        data.update(overrides)

        adaptation = self._score_adaptation(
            data.get("clarity", 0.5),
            data.get("foresight", 0.5),
            data.get("empiricism", 0.5),
        )
        principle = self._principle_preservation(
            data.get("anchor_confidence", 1.0),
            data.get("tri_score", 1.0),
            data.get("ideology_push", False),
        )
        risk = self._residual_risk(
            data.get("layer_scores", {}),
            data.get("tri_score", 1.0),
        )

        return {
            "adaptation_effectiveness": adaptation,
            "principle_preservation": principle,
            "principle_preservation_score": principle,
            "residual_risk": risk,
            "policy_actions": [],  # CULTURAL_PROFILE@1 contract requirement
            "forbidden_hits": [],  # CULTURAL_PROFILE@1 contract requirement
            "consent_required": False,  # CULTURAL_PROFILE@1 contract requirement
        }

    # ------------------------------------------------------------------
    # Internal helpers – formulas migrated from legacy engine
    # ------------------------------------------------------------------
    def _score_adaptation(self, clarity: float, foresight: float, empiricism: float) -> float:
        """Score adaptation effectiveness using weighted cultural methods."""

        w = self.config.methods
        clarity = self._clamp(clarity)
        foresight = self._clamp(foresight)
        empiricism = self._clamp(empiricism)
        score = (
            0.35 * w["scientific_empiricism"] * empiricism
            + 0.25 * w["greek_logic"] * clarity
            + 0.25 * w["indigenous_longterm"] * foresight
            + 0.10 * w["confucian_precision"] * clarity
            + 0.05 * w["buddhist_impermanence"] * (1 - abs(0.5 - foresight) * 2)
        )
        return self._clamp(score)

    def _principle_preservation(
        self, anchor_confidence: float, tri_score: float, ideology_push: bool
    ) -> float:
        """Estimate preservation of foundational principles."""

        penalty = self.config.ideology_penalty if ideology_push else 0.0
        base_penalty = 1.0 - self._clamp(anchor_confidence)
        try:
            tri_score = max(0.0, float(tri_score))
        except (TypeError, ValueError):
            tri_score = 0.5  # Safe default
        penalty += base_penalty / (tri_score + 0.1)
        return self._clamp(1.0 - penalty)

    def _residual_risk(self, layer_scores: Mapping[str, float], tri_score: float) -> float:
        """Combine Slot‑2 risk information with TRI gap."""

        try:
            risk = max(layer_scores.values()) if layer_scores else 0.0
        except Exception:
            risk = 0.0

        try:
            tri_score = float(tri_score)
        except (TypeError, ValueError):
            tri_score = 0.5  # Safe default

        tri_gap = max(0.0, self.config.tri_min_score - tri_score)

        # For very low TRI scores, ensure high residual risk
        if tri_score < 0.3:
            base_risk = max(0.6, 0.5 * risk + 0.5 * tri_gap)
        else:
            base_risk = 0.5 * risk + 0.5 * tri_gap

        return self._clamp(base_risk)

    @staticmethod
    def _clamp(value: float) -> float:
        try:
            return max(0.0, min(1.0, float(value)))
        except (TypeError, ValueError):
            # If conversion fails, return safe default
            return 0.5
