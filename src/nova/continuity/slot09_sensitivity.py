"""Slot09 Sensitivity Adapter - Phase 11.3 Step 4

Maps ORP regime + duration → sensitivity multipliers for Slot09 Distortion Protection.
Pure function, no state, no side effects.

Purpose:
  Reduce detection sensitivity (increase thresholds) during system instability
  to prevent false positives from regime-induced noise, variance, or drift.

Canonical ORP→Sensitivity multiplier table:
  - normal: 1.0 (no adjustment)
  - heightened (<5min): 1.05 (slight relaxation)
  - heightened (≥5min): 1.15 (moderate relaxation)
  - controlled_degradation: 1.30 (reduced sensitivity)
  - emergency_stabilization: 1.50 (strong desensitization)
  - recovery: 1.20 (gradual return to baseline)

Critical Constraints:
  - Multiplicative (scales thresholds UP to reduce sensitivity)
  - Does NOT change detection topology (what is detected)
  - Does NOT override IDS or policy decisions
  - Result multipliers bounded to [1.0, 2.0] (never reduce below baseline)
  - No ORP symbols leaked into Slot09 public API
  - Recovery allows gradual sensitivity return (1.20 vs η=0.25/emotion=0.60)

Implementation Strategy:
  - Apply multipliers to ids_stability_threshold_* and ids_drift_threshold_*
  - Higher multiplier = higher thresholds = less sensitive = fewer false positives
  - Example: normal threshold=0.25, heightened multiplier=1.15 → adjusted=0.29
"""

from __future__ import annotations
from typing import Dict, Tuple


# Canonical sensitivity multiplier table: (regime, duration_threshold_s) → multiplier
# Format: {regime: [(duration_threshold_s, multiplier), ...]}
# Thresholds checked in order; first match wins
# Multipliers > 1.0 reduce sensitivity (increase thresholds)
SENSITIVITY_MULTIPLIER_TABLE: Dict[str, list[Tuple[float, float]]] = {
    "normal": [
        (0.0, 1.0),  # No adjustment
    ],
    "heightened": [
        (300.0, 1.15),  # ≥5min: moderate relaxation
        (0.0, 1.05),    # <5min: slight relaxation
    ],
    "controlled_degradation": [
        (0.0, 1.30),  # Reduced sensitivity
    ],
    "emergency_stabilization": [
        (0.0, 1.50),  # Strong desensitization (avoid noise-driven false positives)
    ],
    "recovery": [
        (0.0, 1.20),  # Gradual return (less conservative than η=0.25)
    ],
}


def compute_sensitivity_multiplier(regime: str, duration_s: float) -> float:
    """Compute sensitivity threshold multiplier from ORP regime + duration.

    Args:
        regime: ORP regime name (normal, heightened, controlled_degradation, emergency_stabilization, recovery)
        duration_s: Time in current regime (seconds)

    Returns:
        Multiplier in [1.0, 2.0] to scale sensitivity thresholds upward (reduce sensitivity)

    Algorithm:
        1. Lookup regime in multiplier table
        2. Find first (threshold, multiplier) where duration_s >= threshold
        3. Return multiplier
        4. Default to 1.0 if regime unknown

    Constraints:
        - Result is purely multiplicative (applied to thresholds, not detections)
        - Multipliers ≥ 1.0 (never make thresholds MORE sensitive)
        - Does NOT change what patterns are detected (only threshold sensitivity)

    Examples:
        >>> compute_sensitivity_multiplier("normal", 1000.0)
        1.0
        >>> compute_sensitivity_multiplier("heightened", 100.0)  # <5min
        1.05
        >>> compute_sensitivity_multiplier("heightened", 400.0)  # ≥5min
        1.15
        >>> compute_sensitivity_multiplier("emergency_stabilization", 50.0)
        1.50
        >>> compute_sensitivity_multiplier("recovery", 100.0)
        1.20
        >>> compute_sensitivity_multiplier("unknown_regime", 100.0)
        1.0
    """
    # Normalize regime name (lowercase, strip whitespace)
    regime = regime.lower().strip()

    # Lookup regime in table
    if regime not in SENSITIVITY_MULTIPLIER_TABLE:
        # Unknown regime - default to no adjustment
        return 1.0

    thresholds = SENSITIVITY_MULTIPLIER_TABLE[regime]

    # Find first matching threshold (list is pre-sorted descending by threshold)
    for threshold_s, multiplier in thresholds:
        if duration_s >= threshold_s:
            return multiplier

    # Fallback (should never reach here if table has 0.0 threshold)
    return 1.0


def apply_sensitivity_scaling(
    base_threshold: float,
    regime: str,
    duration_s: float
) -> float:
    """Apply ORP-based scaling to sensitivity threshold.

    Args:
        base_threshold: Base sensitivity threshold (before scaling)
        regime: Current ORP regime
        duration_s: Time in current regime (seconds)

    Returns:
        Scaled threshold: base_threshold * multiplier, clamped to reasonable bounds

    Constraints:
        - Purely multiplicative (not additive)
        - Multipliers ≥ 1.0 (only reduce sensitivity, never increase)
        - Result bounded to [base_threshold, base_threshold * 2.0]

    Examples:
        >>> apply_sensitivity_scaling(0.25, "normal", 100.0)
        0.25
        >>> apply_sensitivity_scaling(0.25, "heightened", 100.0)  # <5min: 1.05
        0.2625
        >>> apply_sensitivity_scaling(0.25, "emergency_stabilization", 50.0)  # 1.50
        0.375
        >>> apply_sensitivity_scaling(1.0, "heightened", 400.0)  # ≥5min: 1.15
        1.15
    """
    # Compute multiplier
    multiplier = compute_sensitivity_multiplier(regime, duration_s)

    # Apply multiplicative scaling
    threshold_scaled = base_threshold * multiplier

    # Clamp to reasonable bounds (never reduce below baseline, cap at 2x)
    return max(base_threshold, min(base_threshold * 2.0, threshold_scaled))


def get_sensitivity_metadata(regime: str, duration_s: float) -> Dict[str, any]:
    """Get metadata about current sensitivity scaling state.

    Useful for debugging, logging, and metrics.

    Returns:
        {
            "regime": str,
            "duration_s": float,
            "multiplier": float,
            "threshold_matched_s": float,
        }
    """
    multiplier = compute_sensitivity_multiplier(regime, duration_s)

    # Find which threshold was matched
    regime_normalized = regime.lower().strip()
    threshold_matched_s = 0.0

    if regime_normalized in SENSITIVITY_MULTIPLIER_TABLE:
        thresholds = SENSITIVITY_MULTIPLIER_TABLE[regime_normalized]
        for threshold_s, mult in thresholds:
            if duration_s >= threshold_s:
                threshold_matched_s = threshold_s
                break

    return {
        "regime": regime,
        "duration_s": duration_s,
        "multiplier": multiplier,
        "threshold_matched_s": threshold_matched_s,
    }
