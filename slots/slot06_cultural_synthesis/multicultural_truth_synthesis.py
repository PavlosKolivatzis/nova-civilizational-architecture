from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional
from warnings import warn

from .engine import CulturalSynthesisEngine as _CSE
from .adapter import CulturalSynthesisAdapter as _CSA

warn(
    "Slot6: 'multicultural_truth_synthesis' is deprecated; "
    "use 'engine.CulturalSynthesisEngine' and 'adapter.CulturalSynthesisAdapter' instead.",
    DeprecationWarning,
    stacklevel=2,
)


@dataclass
class _CompatResult:
    """Legacy attribute-style view over synthesis metrics."""

    adaptation_effectiveness: float
    principle_preservation: float
    principle_preservation_score: float
    residual_risk: float
    policy_actions: List[str]
    forbidden_hits: List[str]
    consent_required: bool
    version: str

    @classmethod
    def from_metrics(cls, m: Dict[str, Any]) -> "_CompatResult":
        return cls(
            float(m.get("adaptation_effectiveness", 0.0)),
            float(m.get("principle_preservation", m.get("principle_preservation_score", 0.0))),
            float(m.get("principle_preservation_score", 0.0)),
            float(m.get("residual_risk", 1.0)),
            list(m.get("policy_actions", [])),
            list(m.get("forbidden_hits", [])),
            bool(m.get("consent_required", False)),
            str(m.get("version", "")),
        )


def _get(obj: Any, key: str, default: Any) -> Any:
    if isinstance(obj, dict):
        return obj.get(key, default)
    return getattr(obj, key, default)


def _compat_analyze_and_simulate(
    self: _CSE,
    institution_type: str,
    payload: Any,
    options: Optional[Dict[str, Any]] = None,
    profile: Optional[Dict[str, Any]] = None,
    *,
    slot2_result: Optional[Any] = None,
) -> _CompatResult:
    """v7.4.1 compatibility: return attribute object instead of dict."""

    content = payload.get("content") if isinstance(payload, dict) else str(payload)
    tri_score = float(_get(slot2_result, "tri_score", 0.5))
    layer_scores = _get(slot2_result, "layer_scores", {}) or {}
    forbidden_hits = (
        _get(slot2_result, "forbidden_hits", None)
        or _get(slot2_result, "forbidden", [])
        or []
    )

    consent_ok = True
    if isinstance(profile, dict):
        for k in ("consent_ok", "consent", "has_consent"):
            if k in profile:
                consent_ok = bool(profile[k])
                break

    metrics = self.synthesize(
        content,
        tri_score=tri_score,
        layer_scores=layer_scores,
        forbidden_hits=forbidden_hits,
        consent_ok=consent_ok,
        stability_index=_get(slot2_result, "stability_index", None),
    )
    return _CompatResult.from_metrics(metrics)


if not hasattr(_CSE, "_legacy_api_installed"):
    _CSE.analyze_and_simulate = _compat_analyze_and_simulate  # type: ignore[attr-defined]
    _CSE._legacy_api_installed = True  # sentinel


class MulticulturalTruthSynthesis(_CSE):
    """Deprecated alias for CulturalSynthesisEngine with legacy method via monkey patch."""

    pass


class AdaptiveSynthesisEngine(_CSE):
    """Deprecated alias for CulturalSynthesisEngine with legacy method via monkey patch."""

    pass


class MulticulturalTruthSynthesisAdapter(_CSA):
    """Deprecated adapter alias for compatibility."""

    pass


__all__ = [
    "MulticulturalTruthSynthesis",
    "AdaptiveSynthesisEngine",
    "MulticulturalTruthSynthesisAdapter",
]

