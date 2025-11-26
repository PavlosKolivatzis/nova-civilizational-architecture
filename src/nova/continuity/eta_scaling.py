"""Eta (η) Scaling Adapter - Phase 11.3 Step 2

Maps ORP regime + duration → learning rate multiplier for Wisdom Governor.
Pure function, no state, no side effects.

Purpose:
  System becomes more conservative under instability (lower η = slower learning)
  and automatically recovers when stable (higher η = normal learning).

Canonical η scaling table:
  - normal (any duration): 1.0 (no change)
  - heightened (<5min): 0.95 (slight caution)
  - heightened (≥5min): 0.90 (sustained caution)
  - controlled_degradation: 0.75 (reduced learning)
  - emergency_stabilization: 0.50 (conservative)
  - recovery: 0.25 (very conservative, manual mode)

Constraints:
  - Multiplicative scaling: eta_effective = eta_base * eta_scale
  - Never exceeds 1.0
  - Freeze (η=0.0) supersedes all scaling
  - No cross-slot coupling beyond this adapter
"""

from __future__ import annotations
from typing import Dict, Tuple


# Canonical η scaling table: (regime, duration_threshold_s) → scale_factor
# Format: {regime: [(duration_threshold_s, scale_factor), ...]}
# Thresholds are checked in order; first match wins
ETA_SCALING_TABLE: Dict[str, list[Tuple[float, float]]] = {
    "normal": [
        (0.0, 1.0),  # Always 1.0 (no scaling)
    ],
    "heightened": [
        (300.0, 0.90),  # ≥5min: sustained caution
        (0.0, 0.95),    # <5min: slight caution
    ],
    "controlled_degradation": [
        (0.0, 0.75),  # Reduced learning
    ],
    "emergency_stabilization": [
        (0.0, 0.50),  # Conservative
    ],
    "recovery": [
        (0.0, 0.25),  # Very conservative, manual mode
    ],
}


def compute_eta_scale(regime: str, duration_s: float) -> float:
    """Compute η scale factor from ORP regime + duration.

    Args:
        regime: ORP regime name (normal, heightened, controlled_degradation, emergency_stabilization, recovery)
        duration_s: Time in current regime (seconds)

    Returns:
        Scale factor in [0.0, 1.0] to multiply against base η

    Algorithm:
        1. Lookup regime in scaling table
        2. Find first (threshold, scale) where duration_s >= threshold
        3. Return scale factor
        4. Default to 1.0 if regime unknown

    Examples:
        >>> compute_eta_scale("normal", 1000.0)
        1.0
        >>> compute_eta_scale("heightened", 100.0)  # <5min
        0.95
        >>> compute_eta_scale("heightened", 400.0)  # ≥5min
        0.90
        >>> compute_eta_scale("emergency_stabilization", 50.0)
        0.50
        >>> compute_eta_scale("unknown_regime", 100.0)
        1.0
    """
    # Normalize regime name (lowercase, strip whitespace)
    regime = regime.lower().strip()

    # Lookup regime in table
    if regime not in ETA_SCALING_TABLE:
        # Unknown regime - default to no scaling
        return 1.0

    thresholds = ETA_SCALING_TABLE[regime]

    # Find first matching threshold (list is pre-sorted descending by threshold)
    for threshold_s, scale_factor in thresholds:
        if duration_s >= threshold_s:
            return scale_factor

    # Fallback (should never reach here if table has 0.0 threshold)
    return 1.0


def apply_eta_scaling(
    eta_base: float,
    regime: str,
    duration_s: float,
    freeze: bool = False
) -> float:
    """Apply ORP-based scaling to base learning rate.

    Args:
        eta_base: Base learning rate (before scaling)
        regime: Current ORP regime
        duration_s: Time in current regime (seconds)
        freeze: If True, override to 0.0 (freeze supersedes all)

    Returns:
        Effective learning rate: eta_base * scale_factor, clamped to [0.0, 1.0]

    Constraints:
        - Freeze (η=0.0) supersedes all scaling
        - Result never exceeds 1.0
        - Multiplicative scaling (not additive)

    Examples:
        >>> apply_eta_scaling(0.8, "normal", 100.0)
        0.8
        >>> apply_eta_scaling(0.8, "heightened", 100.0)  # <5min: 0.95
        0.76
        >>> apply_eta_scaling(0.8, "emergency_stabilization", 50.0)  # 0.50
        0.4
        >>> apply_eta_scaling(0.8, "normal", 100.0, freeze=True)
        0.0
        >>> apply_eta_scaling(1.2, "normal", 100.0)  # Clamp to 1.0
        1.0
    """
    # Freeze supersedes all
    if freeze:
        return 0.0

    # Compute scale factor
    scale_factor = compute_eta_scale(regime, duration_s)

    # Apply multiplicative scaling
    eta_effective = eta_base * scale_factor

    # Clamp to [0.0, 1.0]
    return max(0.0, min(1.0, eta_effective))


def get_eta_scaling_metadata(regime: str, duration_s: float) -> Dict[str, any]:
    """Get metadata about current η scaling state.

    Useful for debugging, logging, and metrics.

    Returns:
        {
            "regime": str,
            "duration_s": float,
            "scale_factor": float,
            "threshold_matched_s": float,
        }
    """
    scale_factor = compute_eta_scale(regime, duration_s)

    # Find which threshold was matched
    regime_normalized = regime.lower().strip()
    threshold_matched_s = 0.0

    if regime_normalized in ETA_SCALING_TABLE:
        thresholds = ETA_SCALING_TABLE[regime_normalized]
        for threshold_s, scale in thresholds:
            if duration_s >= threshold_s:
                threshold_matched_s = threshold_s
                break

    return {
        "regime": regime,
        "duration_s": duration_s,
        "scale_factor": scale_factor,
        "threshold_matched_s": threshold_matched_s,
    }
