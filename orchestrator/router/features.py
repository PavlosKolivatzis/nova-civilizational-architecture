"""Phase 5.1 LinUCB feature extraction for contextual routing decisions."""

from typing import Dict, Any, List


# Fixed feature set for stable LinUCB dimensions
FEATURES = [
    "tri_drift_z", "system_pressure", "phase_jitter",
    "cultural_residual_risk", "dynamic_half_life_norm",
    "backpressure_level", "transform_rate_hint", "rollback_hint",
    "latency_budget_norm", "error_budget_remaining_norm",
]

FEATURE_DIM = len(FEATURES) + 1  # +1 for bias term


def _clip(x: float, lo: float = 0.0, hi: float = 1.0) -> float:
    """Clip value to [lo, hi] range for bounded features."""
    return max(lo, min(hi, float(x)))


def build_feature_vector(ctx: Dict[str, Any]) -> List[float]:
    """Extract normalized feature vector from routing context.

    Args:
        ctx: Routing context with slot signals and semantic mirror data

    Returns:
        11-dimensional feature vector [features + bias] ∈ [0,1]^10 × {1}
    """
    # Slot04 TRI signals (normalized drift indicators)
    tri_drift = _clip(ctx.get("tri_drift_z", 0.0), 0.0, 3.0) / 3.0

    # Slot07 production control signals
    system_pressure = _clip(ctx.get("system_pressure", 0.0))
    phase_jitter = _clip(ctx.get("phase_jitter", 0.0), 0.0, 0.5) * 2.0
    backpressure_level = _clip(ctx.get("backpressure_level", 0.0))

    # Slot06 cultural synthesis state
    cultural_residual_risk = _clip(ctx.get("cultural_residual_risk", 0.2))

    # Phase 4.1 unlearning dynamics
    dynamic_half_life_norm = _clip(ctx.get("dynamic_half_life_norm", 0.5))

    # Deployment hints and budget constraints
    transform_rate_hint = _clip(ctx.get("transform_rate_hint", 0.2))
    rollback_hint = 1.0 if ctx.get("rollback_expected", False) else 0.0
    latency_budget_norm = _clip(ctx.get("latency_budget_norm", 0.5))
    error_budget_remaining_norm = _clip(ctx.get("error_budget_remaining_norm", 0.5))

    # Bias term for linear model intercept
    bias = 1.0

    return [
        tri_drift, system_pressure, phase_jitter,
        cultural_residual_risk, dynamic_half_life_norm,
        backpressure_level, transform_rate_hint, rollback_hint,
        latency_budget_norm, error_budget_remaining_norm,
        bias
    ]


def normalize_immediate_reward(latency_s: float, tri_delta: float) -> float:
    """Normalize immediate feedback to [-1, +1] reward signal.

    Args:
        latency_s: Request latency in seconds
        tri_delta: TRI score change (positive = improvement)

    Returns:
        Shaped reward: +tri_delta_norm - latency_norm
    """
    # Normalize TRI delta: assume [-0.2, +0.2] typical range
    tri_delta_norm = _clip(tri_delta, -0.2, 0.2) / 0.2

    # Normalize latency: assume [0, 5.0s] reasonable range, invert (lower is better)
    latency_norm = _clip(latency_s, 0.0, 5.0) / 5.0

    return tri_delta_norm - latency_norm


def normalize_deployment_reward(feedback: Dict[str, Any]) -> float:
    """Normalize deployment feedback to [-1, +1] reward signal.

    Args:
        feedback: Slot10 deployment feedback with slo_ok, rollback, etc.

    Returns:
        Shaped reward: +slo_ok - rollback - error_rate - transform_burden
    """
    slo_ok = 1.0 if feedback.get("slo_ok", False) else -1.0
    rollback_penalty = -1.0 if feedback.get("rollback", False) else 0.0
    error_penalty = -float(feedback.get("error_rate", 0.0))

    # Transform rate as burden: higher = more cultural work required
    transform_burden = -float(feedback.get("transform_rate", 0.0)) * 0.5

    return slo_ok + rollback_penalty + error_penalty + transform_burden