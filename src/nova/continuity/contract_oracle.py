"""Contract Oracle - Independent ORP Implementation (Phase 12)

Pure implementation of orp@1.yaml contract specification.
Used for differential testing to ensure OperationalRegimePolicy fidelity.

This module MUST remain independent of operational_regime.py.
No shared logic, no imports from operational_regime.py.
Any divergence between oracle and ORP implementation = bug or spec ambiguity.
"""

from typing import Dict, Tuple

# ---------- Contract Constants (from orp@1.yaml) ----------

# Regime score ranges [low, high)
REGIME_THRESHOLDS = {
    "normal": (0.0, 0.30),
    "heightened": (0.30, 0.50),
    "controlled_degradation": (0.50, 0.70),
    "emergency_stabilization": (0.70, 0.85),
    "recovery": (0.85, 1.0),
}

# Signal weights for regime_score calculation
SIGNAL_WEIGHTS = {
    "urf_composite_risk": 0.30,
    "mse_meta_instability": 0.25,
    "predictive_collapse_risk": 0.20,
    "consistency_gap": 0.15,
    "csi_continuity_index": 0.10,  # Inverted: (1.0 - CSI)
}

# Hysteresis and timing parameters
DOWNGRADE_HYSTERESIS = 0.05  # Score must drop 0.05 below threshold to downgrade
MIN_REGIME_DURATION_S = 300.0  # 5 minutes minimum before downgrade

# Regime severity order (for upgrade/downgrade detection)
REGIME_ORDER = [
    "normal",
    "heightened",
    "controlled_degradation",
    "emergency_stabilization",
    "recovery",
]


# ---------- Pure Functions ----------


def clamp(value: float, min_val: float = 0.0, max_val: float = 1.0) -> float:
    """Clamp value to [min_val, max_val]."""
    return max(min_val, min(max_val, value))


def compute_regime_score_from_contract(
    factors: Dict[str, float],
    weights: Dict[str, float] = SIGNAL_WEIGHTS,
) -> float:
    """Pure implementation of weighted regime score calculation with CSI inversion.

    Per orp@1.yaml:
    - regime_score = weighted sum of contributing_factors
    - All inputs clamped to [0.0, 1.0]
    - CSI inverted: (1.0 - csi_continuity_index)

    Args:
        factors: Contributing factors dict with keys:
            - urf_composite_risk
            - mse_meta_instability
            - predictive_collapse_risk
            - consistency_gap
            - csi_continuity_index
        weights: Signal weights (default from contract)

    Returns:
        Regime score in [0.0, 1.0]
    """
    # Extract and clamp factors
    urf = clamp(factors.get("urf_composite_risk", 0.0))
    mse = clamp(factors.get("mse_meta_instability", 0.0))
    pred = clamp(factors.get("predictive_collapse_risk", 0.0))
    gap = clamp(factors.get("consistency_gap", 0.0))
    csi = clamp(factors.get("csi_continuity_index", 1.0))

    # Compute weighted sum with CSI inverted
    score = (
        urf * weights["urf_composite_risk"]
        + mse * weights["mse_meta_instability"]
        + pred * weights["predictive_collapse_risk"]
        + gap * weights["consistency_gap"]
        + (1.0 - csi) * weights["csi_continuity_index"]  # Inverted
    )

    return clamp(score)


def classify_regime_from_contract(
    regime_score: float,
    current_regime: str,
    time_in_regime_s: float,
    hysteresis: float = DOWNGRADE_HYSTERESIS,
    min_duration_s: float = MIN_REGIME_DURATION_S,
    thresholds: Dict[str, Tuple[float, float]] = REGIME_THRESHOLDS,
) -> str:
    """Pure implementation of orp@1.yaml regime classification rules.

    Per orp@1.yaml thresholds section:
    - Upgrade: Immediate if score crosses threshold upward
    - Downgrade: Only if BOTH conditions met:
        1. Score < (target_regime_upper_threshold - hysteresis)
        2. time_in_regime_s >= min_duration_s
    - Boundary: Score exactly at threshold → choose higher regime

    Args:
        regime_score: Composite severity score [0.0, 1.0]
        current_regime: Current regime name
        time_in_regime_s: Seconds in current regime
        hysteresis: Downgrade hysteresis (default 0.05)
        min_duration_s: Min duration before downgrade (default 300.0)
        thresholds: Regime score ranges

    Returns:
        Regime name (str)
    """
    # Find regime matching score (upgrade case)
    target_regime = None
    for regime, (low, high) in thresholds.items():
        if low <= regime_score < high:
            target_regime = regime
            break

    # Score >= 1.0 or not matched → assign RECOVERY
    if target_regime is None:
        target_regime = "recovery"

    # Check if upgrade (score increased to higher severity regime)
    current_idx = REGIME_ORDER.index(current_regime)
    target_idx = REGIME_ORDER.index(target_regime)

    if target_idx > current_idx:
        # Upgrade immediately
        return target_regime

    if target_idx < current_idx:
        # Potential downgrade - check hysteresis and duration
        target_upper_threshold = thresholds[target_regime][1]
        hysteresis_threshold = target_upper_threshold - hysteresis

        if regime_score >= hysteresis_threshold:
            # Not below hysteresis, stay in current regime
            return current_regime

        if time_in_regime_s < min_duration_s:
            # Too soon to downgrade, stay in current regime
            return current_regime

        # Downgrade allowed
        return target_regime

    # target_idx == current_idx - no change
    return current_regime


def compute_and_classify(
    factors: Dict[str, float],
    current_regime: str = "normal",
    time_in_regime_s: float = 0.0,
) -> Dict[str, any]:
    """Combined score computation and regime classification.

    Args:
        factors: Contributing factors dict
        current_regime: Current regime name
        time_in_regime_s: Seconds in current regime

    Returns:
        Dict with:
            - regime_score: Computed score
            - regime: Classified regime
    """
    score = compute_regime_score_from_contract(factors)
    regime = classify_regime_from_contract(score, current_regime, time_in_regime_s)

    return {
        "regime_score": score,
        "regime": regime,
    }
