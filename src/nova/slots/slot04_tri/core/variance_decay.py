"""
Variance Decay Model for Phase 7.0 Temporal Resonance

Computes temporal decay weights from sealed Phase 6.0 belief variance data.
Implements the core decay function: decay_weight = exp(-variance × temporal_distance)

All computations are read-only derivatives of archived belief states.
"""

import math
from typing import List, Tuple, Optional
from datetime import datetime, timedelta

from .temporal_schema import TemporalBeliefEntry


class VarianceDecayModel:
    """
    Computes temporal decay weights for belief propagation.

    Transforms belief variance from Phase 6.0 archives into temporal attenuation
    factors that enable resonance-aware decision making.
    """

    def __init__(self, half_life_hours: float = 24.0):
        """
        Initialize decay model.

        Args:
            half_life_hours: Expected half-life for decay weighting (default: 24h)
        """
        self.half_life_hours = half_life_hours
        # Pre-compute decay constant for efficiency
        self.decay_constant = math.log(2) / half_life_hours

    def compute_decay_weight(self, variance: float, temporal_distance: float) -> float:
        """
        Compute temporal decay weight from variance and time distance.

        Formula: decay_weight = exp(-variance × temporal_distance)

        Args:
            variance: Belief variance from Phase 6.0 (0.0 = certain, higher = uncertain)
            temporal_distance: Time distance in hours from reference point

        Returns:
            Decay weight between 0.0 and 1.0 (1.0 = no decay, 0.0 = complete attenuation)
        """
        if variance < 0:
            raise ValueError("Variance must be non-negative")
        if temporal_distance < 0:
            raise ValueError("Temporal distance must be non-negative")

        # Core decay formula: exp(-variance × temporal_distance)
        decay_factor = variance * temporal_distance
        weight = math.exp(-decay_factor)

        # Clamp to reasonable bounds to prevent numerical issues
        return max(0.0, min(1.0, weight))

    def compute_half_life(self, variance: float) -> float:
        """
        Compute effective half-life for given variance level.

        The half-life is the time when decay_weight = 0.5

        Args:
            variance: Belief variance level

        Returns:
            Half-life in hours (time for weight to decay to 0.5)
        """
        if variance <= 0:
            return float('inf')  # No decay for zero variance

        # Solve: 0.5 = exp(-variance × t_half)
        # t_half = -ln(0.5) / variance = ln(2) / variance
        return math.log(2) / variance

    def batch_compute_weights(self,
                            belief_entries: List[Tuple[float, float]]
                            ) -> List[float]:
        """
        Compute decay weights for multiple belief entries.

        Args:
            belief_entries: List of (variance, temporal_distance) tuples

        Returns:
            List of corresponding decay weights
        """
        return [self.compute_decay_weight(v, t) for v, t in belief_entries]

    def create_temporal_entries(self,
                               belief_states: List[Tuple[datetime, float, float]],
                               reference_time: datetime,
                               slot_id: str,
                               phase_commit: str) -> List[TemporalBeliefEntry]:
        """
        Create temporal belief entries from raw belief state data.

        Args:
            belief_states: List of (timestamp, mean, variance) tuples from archives
            reference_time: Reference point for temporal distance calculation
            slot_id: Source slot identifier
            phase_commit: Phase 6.0 commit hash for provenance

        Returns:
            List of TemporalBeliefEntry objects with computed decay weights
        """
        entries = []

        for timestamp, mean, variance in belief_states:
            temporal_distance = (timestamp - reference_time).total_seconds() / 3600.0

            # Default resonance coefficient (will be refined by coupling engine)
            resonance_coeff = 1.0

            entry = TemporalBeliefEntry(
                timestamp=timestamp,
                belief_mean=mean,
                belief_variance=variance,
                temporal_distance=max(0, temporal_distance),  # Ensure non-negative
                decay_weight=0.0,  # Will be computed by validator
                resonance_coefficient=resonance_coeff,
                slot_id=slot_id,
                phase_commit=phase_commit
            )

            entries.append(entry)

        return entries

    def analyze_decay_characteristics(self,
                                    variance_range: Tuple[float, float] = (0.01, 1.0),
                                    time_range: Tuple[float, float] = (0, 168),  # 0-7 days
                                    steps: int = 50) -> dict:
        """
        Analyze decay characteristics across variance and time ranges.

        Useful for understanding system behavior and setting appropriate thresholds.

        Args:
            variance_range: Min/max variance to analyze
            time_range: Min/max time in hours to analyze
            steps: Number of analysis points

        Returns:
            Dictionary with decay analysis results
        """
        variances = [variance_range[0] + i * (variance_range[1] - variance_range[0]) / (steps - 1)
                    for i in range(steps)]
        times = [time_range[0] + i * (time_range[1] - time_range[0]) / (steps - 1)
                for i in range(steps)]

        # Compute decay surface
        decay_surface = []
        for v in variances:
            row = [self.compute_decay_weight(v, t) for t in times]
            decay_surface.append(row)

        # Compute half-lives
        half_lives = [self.compute_half_life(v) for v in variances]

        return {
            'variance_range': variance_range,
            'time_range': time_range,
            'half_lives': half_lives,
            'decay_surface': decay_surface,
            'expected_half_life_avg': sum(half_lives) / len(half_lives)
        }


# Global instance for system-wide use
default_decay_model = VarianceDecayModel(half_life_hours=24.0)