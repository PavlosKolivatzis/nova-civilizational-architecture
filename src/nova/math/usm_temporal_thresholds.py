"""
Temporal USM Thresholds (Phase 14.5 Observation + Phase 14 min_turns Calibration)

Classification logic for temporal USM state based on C_t and rho_t values.

IMPORTANT:
- The C_t and rho_t band thresholds (extractive_C, protective_C, extractive_rho,
  protective_rho) remain derived from Phase 14.5 pilot observation and may be
  refined with additional evidence.
- The warm-up length `min_turns=3` has been validated and frozen via Phase 14
  K-sweep calibration on RT-027/RT-028/RT-030 (extraction) and RT-032/RT-033
  (benign); see docs/specs/phase14_min_turns_calibration.md.

Validation Criteria (bands):
- Misclassification rate < 50% in first 100 sessions
- If exceeded: STOP and run full calibration with diverse conversations

See also:
- docs/specs/phase14_5_observation_protocol.md
- docs/specs/phase14_min_turns_calibration.md
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

StateClass = Literal["warming_up", "extractive", "consensus", "collaborative", "neutral"]


@dataclass(frozen=True)
class TemporalThresholds:
    """
    Thresholds for temporal USM classification.

    Attributes:
        extractive_C: C_t threshold for extractive collapse (high collapse)
        protective_C: C_t threshold for protective patterns (distributed structure)
        extractive_rho: rho_t threshold for low reciprocity (one-way flow)
        protective_rho: rho_t threshold for high reciprocity (balanced exchange)
        min_turns: Minimum turns required before classification (warm-up period)
    """

    extractive_C: float = 0.18      # ~60% of instantaneous (0.3)
    protective_C: float = -0.12     # ~60% of instantaneous (-0.2)
    extractive_rho: float = 0.25    # Low reciprocity cutoff
    protective_rho: float = 0.6     # High reciprocity baseline
    min_turns: int = 3              # Warm-up period before classification (validated in Phase 14 min_turns calibration)


# Default thresholds (Phase 14.5 bands + Phase 14 min_turns calibration)
DEFAULT_THRESHOLDS = TemporalThresholds()


def classify_temporal_state(
    C_t: float,
    rho_t: float,
    turn_count: int,
    thresholds: TemporalThresholds = DEFAULT_THRESHOLDS,
) -> StateClass:
    """
    Classify conversation state from temporal USM metrics.

    States:
        warming_up: Insufficient turns for reliable classification
        extractive: High collapse + low reciprocity (hierarchical control)
        consensus: Protective collapse + low reciprocity (aligned cooperation)
        collaborative: Protective collapse + high reciprocity (active negotiation)
        neutral: Within normal operational range

    Args:
        C_t: Temporal collapse score
        rho_t: Temporal equilibrium ratio
        turn_count: Number of turns processed so far
        thresholds: Classification thresholds (default: Phase 14.5 provisional)

    Returns:
        State classification string

    Note:
        This logic distinguishes consensus from extraction using combined signals:
        - Both show low reciprocity (rho_t < 0.25)
        - Extraction: C_t > 0.18 (hierarchical structure)
        - Consensus: C_t < -0.12 (protective structure)
    """
    # Early conversation: insufficient data
    if turn_count < thresholds.min_turns:
        return "warming_up"

    # Extractive: High collapse + low reciprocity
    # (Hierarchical control, one-way information flow)
    if C_t >= thresholds.extractive_C and rho_t < thresholds.extractive_rho:
        return "extractive"

    # Consensus: Protective collapse + low reciprocity
    # (Aligned cooperation, no active tension - structurally similar to extraction)
    if C_t <= thresholds.protective_C and rho_t < thresholds.extractive_rho:
        return "consensus"

    # Collaborative: Protective + high reciprocity
    # (Active negotiation, balanced exchange, reciprocal power flow)
    if C_t <= thresholds.protective_C and rho_t >= thresholds.protective_rho:
        return "collaborative"

    # Neutral: Within normal operational range
    return "neutral"


__all__ = [
    "TemporalThresholds",
    "DEFAULT_THRESHOLDS",
    "StateClass",
    "classify_temporal_state",
]
