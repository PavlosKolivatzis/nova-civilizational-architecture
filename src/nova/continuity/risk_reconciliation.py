"""
Unified Risk Field (URF) — Risk Reconciliation Calculator

Phase 9 integration: Reconcile RRI (epistemic) and predictive_collapse_risk (temporal)
into unified risk signal for governance and routing.
"""

from datetime import datetime, timezone
from typing import Dict, Optional


def _clamp(value: float, min_val: float = 0.0, max_val: float = 1.0) -> float:
    """Clamp value to [min_val, max_val] range."""
    return max(min_val, min(max_val, value))


def compute_risk_alignment(
    rri: float,
    collapse_risk: float,
    weights: Optional[Dict[str, float]] = None
) -> Dict:
    """
    Compute Unified Risk Field from RRI and collapse_risk.

    Args:
        rri: Reflective Resonance Index [0.0, 1.0]
        collapse_risk: Predictive collapse risk [0.0, 1.0]
        weights: Optional custom weights (default: {rri: 0.4, collapse_risk: 0.6})

    Returns:
        Dictionary with URF components:
        - rri: normalized RRI
        - predictive_collapse_risk: normalized collapse_risk
        - risk_gap: abs(rri - collapse_risk)
        - alignment_score: 1.0 - risk_gap
        - composite_risk: weighted mean
        - weights: fusion weights
        - timestamp: ISO8601 UTC timestamp
    """
    # Normalize inputs to [0.0, 1.0]
    rri_norm = _clamp(rri)
    collapse_norm = _clamp(collapse_risk)

    # Default weights (temporal risk weighted higher)
    if weights is None:
        weights = {"rri": 0.4, "collapse_risk": 0.6}

    # Compute gap and alignment
    risk_gap = abs(rri_norm - collapse_norm)
    alignment_score = 1.0 - risk_gap

    # Weighted fusion
    w_rri = weights.get("rri", 0.4)
    w_collapse = weights.get("collapse_risk", 0.6)
    composite_risk = (w_rri * rri_norm) + (w_collapse * collapse_norm)

    return {
        "rri": rri_norm,
        "predictive_collapse_risk": collapse_norm,
        "risk_gap": _clamp(risk_gap),
        "alignment_score": _clamp(alignment_score),
        "composite_risk": _clamp(composite_risk),
        "weights": {"rri": w_rri, "collapse_risk": w_collapse},
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


def get_unified_risk_field() -> Dict:
    """
    Query current RRI and collapse_risk gauges and compute URF.

    Reads from:
    - orchestrator.rri.RRI_GAUGE
    - orchestrator.prometheus_metrics.predictive_collapse_risk_gauge

    Returns:
        URF breakdown dictionary (see compute_risk_alignment)
    """
    try:
        # Import lazily to avoid circular dependencies
        from nova.orchestrator.rri import RRI_GAUGE
        from nova.orchestrator.prometheus_metrics import predictive_collapse_risk_gauge

        # Read current gauge values
        rri_value = RRI_GAUGE._value._value if hasattr(RRI_GAUGE, '_value') else 0.0
        collapse_value = predictive_collapse_risk_gauge._value._value if hasattr(predictive_collapse_risk_gauge, '_value') else 0.0

        # Compute URF
        urf = compute_risk_alignment(rri_value, collapse_value)

        # Add metadata
        urf["metadata"] = {
            "rri_source": "orchestrator.rri.RRI_GAUGE",
            "collapse_risk_source": "orchestrator.prometheus_metrics.predictive_collapse_risk_gauge",
            "version": "1.0.0"
        }

        return urf

    except ImportError as e:
        # Fallback if gauges not available
        return {
            "rri": 0.0,
            "predictive_collapse_risk": 0.0,
            "risk_gap": 0.0,
            "alignment_score": 1.0,
            "composite_risk": 0.0,
            "weights": {"rri": 0.4, "collapse_risk": 0.6},
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "metadata": {
                "error": f"Gauge import failed: {e}",
                "version": "1.0.0"
            }
        }
