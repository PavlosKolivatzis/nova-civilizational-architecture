"""Emotional Posture Adapter - Phase 11.3 Step 3

Maps ORP regime + duration → emotional multiplier for Slot03 Emotional Matrix.
Pure function, no state, no side effects.

Purpose:
  Reduce emotional amplitude/variance during system instability (heightened+ regimes)
  to prevent emotional volatility from amplifying drift, misalignment, or variance.

Canonical ORP→Emotion multiplier table:
  - normal: 1.0 (no constriction)
  - heightened (<5min): 0.95 (slight damping)
  - heightened (≥5min): 0.85 (moderate damping)
  - controlled_degradation: 0.70 (reduced amplitude)
  - emergency_stabilization: 0.50 (strong constriction)
  - recovery: 0.60 (gradual recovery, not too restrictive)

Critical Constraints:
  - Purely multiplicative (scales intensity, not topology)
  - Does NOT change emotional topology (joy/sadness/etc. preserved)
  - Does NOT override URF/MSE/η
  - Result bounded to [0.0, 1.0]
  - No ORP symbols leaked into emotional metadata
  - Recovery allows gradual amplitude return (0.60 not 0.25 like η)
"""

from __future__ import annotations
from typing import Dict, Tuple


# Canonical emotional multiplier table: (regime, duration_threshold_s) → multiplier
# Format: {regime: [(duration_threshold_s, multiplier), ...]}
# Thresholds checked in order; first match wins
EMOTIONAL_MULTIPLIER_TABLE: Dict[str, list[Tuple[float, float]]] = {
    "normal": [
        (0.0, 1.0),  # No constriction
    ],
    "heightened": [
        (300.0, 0.85),  # ≥5min: moderate damping
        (0.0, 0.95),    # <5min: slight damping
    ],
    "controlled_degradation": [
        (0.0, 0.70),  # Reduced amplitude
    ],
    "emergency_stabilization": [
        (0.0, 0.50),  # Strong constriction
    ],
    "recovery": [
        (0.0, 0.60),  # Gradual recovery (not as restrictive as η=0.25)
    ],
}


def compute_emotional_multiplier(regime: str, duration_s: float) -> float:
    """Compute emotional amplitude multiplier from ORP regime + duration.

    Args:
        regime: ORP regime name (normal, heightened, controlled_degradation, emergency_stabilization, recovery)
        duration_s: Time in current regime (seconds)

    Returns:
        Multiplier in [0.0, 1.0] to scale emotional intensity/amplitude

    Algorithm:
        1. Lookup regime in multiplier table
        2. Find first (threshold, multiplier) where duration_s >= threshold
        3. Return multiplier
        4. Default to 1.0 if regime unknown

    Constraints:
        - Result is purely multiplicative (applied to intensity, not valence)
        - Preserves emotional topology (joy stays joy, sadness stays sadness)
        - Does NOT change which emotion is active (only scales magnitude)

    Examples:
        >>> compute_emotional_multiplier("normal", 1000.0)
        1.0
        >>> compute_emotional_multiplier("heightened", 100.0)  # <5min
        0.95
        >>> compute_emotional_multiplier("heightened", 400.0)  # ≥5min
        0.85
        >>> compute_emotional_multiplier("emergency_stabilization", 50.0)
        0.50
        >>> compute_emotional_multiplier("recovery", 100.0)
        0.60
        >>> compute_emotional_multiplier("unknown_regime", 100.0)
        1.0
    """
    # Normalize regime name (lowercase, strip whitespace)
    regime = regime.lower().strip()

    # Lookup regime in table
    if regime not in EMOTIONAL_MULTIPLIER_TABLE:
        # Unknown regime - default to no constriction
        return 1.0

    thresholds = EMOTIONAL_MULTIPLIER_TABLE[regime]

    # Find first matching threshold (list is pre-sorted descending by threshold)
    for threshold_s, multiplier in thresholds:
        if duration_s >= threshold_s:
            return multiplier

    # Fallback (should never reach here if table has 0.0 threshold)
    return 1.0


def apply_emotional_constriction(
    intensity: float,
    regime: str,
    duration_s: float
) -> float:
    """Apply ORP-based constriction to emotional intensity.

    Args:
        intensity: Base emotional intensity (before constriction)
        regime: Current ORP regime
        duration_s: Time in current regime (seconds)

    Returns:
        Constricted intensity: intensity * multiplier, clamped to [0.0, 1.0]

    Constraints:
        - Purely multiplicative (not additive)
        - Preserves emotional topology (which emotion is active)
        - Does NOT change valence (positive/negative direction)
        - Result bounded to [0.0, 1.0]

    Examples:
        >>> apply_emotional_constriction(0.8, "normal", 100.0)
        0.8
        >>> apply_emotional_constriction(0.8, "heightened", 100.0)  # <5min: 0.95
        0.76
        >>> apply_emotional_constriction(0.8, "emergency_stabilization", 50.0)  # 0.50
        0.4
        >>> apply_emotional_constriction(1.2, "normal", 100.0)  # Clamp to 1.0
        1.0
        >>> apply_emotional_constriction(-0.5, "normal", 100.0)  # Clamp to 0.0
        0.0
    """
    # Compute multiplier
    multiplier = compute_emotional_multiplier(regime, duration_s)

    # Apply multiplicative constriction
    intensity_constricted = intensity * multiplier

    # Clamp to [0.0, 1.0]
    return max(0.0, min(1.0, intensity_constricted))


def get_emotional_posture_metadata(regime: str, duration_s: float) -> Dict[str, any]:
    """Get metadata about current emotional posture state.

    Useful for debugging, logging, and metrics.

    Returns:
        {
            "regime": str,
            "duration_s": float,
            "multiplier": float,
            "threshold_matched_s": float,
        }
    """
    multiplier = compute_emotional_multiplier(regime, duration_s)

    # Find which threshold was matched
    regime_normalized = regime.lower().strip()
    threshold_matched_s = 0.0

    if regime_normalized in EMOTIONAL_MULTIPLIER_TABLE:
        thresholds = EMOTIONAL_MULTIPLIER_TABLE[regime_normalized]
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
