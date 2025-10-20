"""
Temporal Belief Schema for Phase 7.0 Temporal Resonance

Extends BeliefState with time-series metadata for temporal coherence analysis.
All temporal data derived from sealed Phase 6.0 belief variance archives.
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, validator
import math


class TemporalBeliefEntry(BaseModel):
    """
    Single temporal belief entry with decay weighting.

    Represents a belief state at a specific point in time with computed
    temporal decay weight derived from Phase 6.0 variance data.
    """

    timestamp: datetime = Field(..., description="UTC timestamp of belief measurement")
    belief_mean: float = Field(..., ge=0.0, le=1.0, description="Belief confidence mean (0.0-1.0)")
    belief_variance: float = Field(..., ge=0.0, description="Belief uncertainty variance from Phase 6.0")
    temporal_distance: float = Field(..., ge=0.0, description="Time distance in hours from reference point")
    decay_weight: float = Field(..., ge=0.0, le=1.0, description="Computed temporal decay weight")
    resonance_coefficient: float = Field(..., ge=0.0, le=2.0, description="Cross-temporal coupling strength")

    slot_id: str = Field(..., description="Source slot identifier (e.g., 'slot04', 'slot07')")
    phase_commit: str = Field(..., description="Phase 6.0 commit hash for provenance")

    @validator('decay_weight', pre=True, always=True)
    def compute_decay_weight(cls, v, values):
        """Compute decay weight from variance and temporal distance."""
        if 'belief_variance' in values and 'temporal_distance' in values:
            variance = values['belief_variance']
            distance = values['temporal_distance']
            # decay_weight = exp(-variance × temporal_distance)
            return math.exp(-variance * distance)
        return v

    class Config:
        """Pydantic configuration."""
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class TemporalResonanceWindow(BaseModel):
    """
    Time-windowed collection of temporal belief entries.

    Represents a coherent temporal window for resonance analysis.
    """

    window_start: datetime
    window_end: datetime
    entries: list[TemporalBeliefEntry] = Field(..., min_items=1)
    trsi_baseline: float = Field(..., ge=0.0, le=1.0, description="Computed TRSI for this window")

    @property
    def duration_hours(self) -> float:
        """Compute window duration in hours."""
        return (self.window_end - self.window_start).total_seconds() / 3600

    @property
    def average_decay_weight(self) -> float:
        """Compute average decay weight across entries."""
        if not self.entries:
            return 0.0
        return sum(entry.decay_weight for entry in self.entries) / len(self.entries)

    @property
    def average_resonance_coefficient(self) -> float:
        """Compute average resonance coefficient across entries."""
        if not self.entries:
            return 0.0
        return sum(entry.resonance_coefficient for entry in self.entries) / len(self.entries)


class TemporalResonanceMetrics(BaseModel):
    """
    Aggregated temporal resonance metrics for monitoring.

    Computed from temporal belief windows for system observability.
    """

    current_trsi: float = Field(..., ge=0.0, le=1.0, description="Current TRSI value")
    trsi_trend_24h: float = Field(..., description="TRSI change over 24 hours")
    average_decay_weight: float = Field(..., ge=0.0, le=1.0)
    average_coupling_strength: float = Field(..., ge=0.0, le=2.0)
    temporal_coherence_score: float = Field(..., ge=0.0, le=1.0)

    last_updated: datetime
    window_count: int = Field(..., ge=0)
    total_entries_processed: int = Field(..., ge=0)

    @validator('temporal_coherence_score', pre=True, always=True)
    def compute_coherence(cls, v, values):
        """Compute temporal coherence from TRSI and decay metrics."""
        if 'current_trsi' in values and 'average_decay_weight' in values:
            trsi = values['current_trsi']
            decay = values['average_decay_weight']
            # Simple coherence metric: harmonic mean of TRSI and decay
            if trsi > 0 and decay > 0:
                return 2 * trsi * decay / (trsi + decay)
        return 0.5  # Default baseline