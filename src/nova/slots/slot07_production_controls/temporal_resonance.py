"""
Temporal Resonance Engine for Phase 7.0

Computes Temporal Resonance Stability Index (TRSI) from decay-weighted belief propagation.
Implements cross-temporal coupling and resonance amplification for civilizational-scale coherence.

All computations derive from sealed Phase 6.0 belief variance archives.
"""

import math
import statistics
from typing import List, Dict, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass

from nova.slots.slot04_tri.core.temporal_schema import (
    TemporalBeliefEntry,
    TemporalResonanceWindow,
    TemporalResonanceMetrics
)
from nova.slots.slot04_tri.core.variance_decay import VarianceDecayModel


@dataclass
class ResonanceCouplingResult:
    """Result of resonance coupling computation."""
    trsi_value: float
    coupling_strength: float
    coherence_score: float
    window_size: int
    computation_timestamp: datetime


class TemporalResonanceEngine:
    """
    Computes temporal resonance from belief propagation patterns.

    Transforms temporal decay weights into resonance stability metrics,
    enabling predictive adaptation across time horizons.
    """

    def __init__(self,
                 decay_model: Optional[VarianceDecayModel] = None,
                 coupling_threshold: float = 0.8,
                 resonance_amplification: float = 1.5):
        """
        Initialize resonance engine.

        Args:
            decay_model: Variance decay model instance
            coupling_threshold: Minimum coupling strength for resonance (0.0-1.0)
            resonance_amplification: Amplification factor for strong couplings (1.0-2.0)
        """
        self.decay_model = decay_model or VarianceDecayModel()
        self.coupling_threshold = coupling_threshold
        self.resonance_amplification = resonance_amplification

        # Internal state for metrics tracking
        self._last_trsi = 0.5  # Baseline starting value
        self._trsi_history: List[Tuple[datetime, float]] = []

    def compute_trsi(self, temporal_entries: List[TemporalBeliefEntry]) -> float:
        """
        Compute Temporal Resonance Stability Index from belief entries.

        TRSI = Σ(decay_weight × resonance_coefficient) / N

        Args:
            temporal_entries: List of temporal belief entries

        Returns:
            TRSI value between 0.0 (no resonance) and 1.0 (perfect temporal alignment)
        """
        if not temporal_entries:
            return 0.5  # Neutral baseline

        # Compute weighted resonance scores
        resonance_scores = []
        total_weight = 0.0

        for entry in temporal_entries:
            # Weight by decay factor and coupling coefficient
            weight = entry.decay_weight * entry.resonance_coefficient
            resonance_scores.append(weight)
            total_weight += weight

        if total_weight == 0:
            return 0.5  # Neutral when no valid weights

        # Normalize to 0.0-1.0 range
        raw_trsi = sum(resonance_scores) / len(resonance_scores)

        # Apply resonance amplification for strong couplings
        if raw_trsi > self.coupling_threshold:
            amplification_factor = self.resonance_amplification
            amplified = raw_trsi * amplification_factor
            # Clamp to prevent overshoot
            trsi = min(1.0, amplified)
        else:
            trsi = raw_trsi

        # Update internal state
        self._last_trsi = trsi
        self._trsi_history.append((datetime.utcnow(), trsi))

        # Keep history bounded (last 1000 entries)
        if len(self._trsi_history) > 1000:
            self._trsi_history = self._trsi_history[-1000:]

        return trsi

    def compute_resonance_coupling(self,
                                 window_entries: List[TemporalBeliefEntry]
                                 ) -> ResonanceCouplingResult:
        """
        Compute comprehensive resonance coupling for a time window.

        Args:
            window_entries: Temporal entries within a coherent time window

        Returns:
            Detailed coupling analysis result
        """
        trsi = self.compute_trsi(window_entries)

        # Compute coupling strength (average resonance coefficient)
        if window_entries:
            coupling_strength = sum(e.resonance_coefficient for e in window_entries) / len(window_entries)
        else:
            coupling_strength = 0.0

        # Compute coherence score (harmonic mean of TRSI and coupling)
        if trsi > 0 and coupling_strength > 0:
            coherence_score = 2 * trsi * coupling_strength / (trsi + coupling_strength)
        else:
            coherence_score = 0.0

        return ResonanceCouplingResult(
            trsi_value=trsi,
            coupling_strength=coupling_strength,
            coherence_score=coherence_score,
            window_size=len(window_entries),
            computation_timestamp=datetime.utcnow()
        )

    def analyze_temporal_patterns(self,
                                entries: List[TemporalBeliefEntry],
                                window_hours: float = 24.0) -> Dict[str, float]:
        """
        Analyze temporal patterns across sliding windows.

        Args:
            entries: All available temporal entries
            window_hours: Window size in hours for pattern analysis

        Returns:
            Dictionary of temporal pattern metrics
        """
        if not entries:
            return {
                'average_trsi': 0.5,
                'trsi_volatility': 0.0,
                'temporal_coherence': 0.0,
                'resonance_strength': 0.0
            }

        # Sort entries by timestamp
        sorted_entries = sorted(entries, key=lambda e: e.timestamp)

        # Create sliding windows
        windows = []
        window_start = sorted_entries[0].timestamp

        while window_start < sorted_entries[-1].timestamp:
            window_end = window_start + timedelta(hours=window_hours)
            window_entries = [
                e for e in sorted_entries
                if window_start <= e.timestamp < window_end
            ]

            if window_entries:
                coupling_result = self.compute_resonance_coupling(window_entries)
                windows.append(coupling_result)

            window_start = window_end

        if not windows:
            return {
                'average_trsi': 0.5,
                'trsi_volatility': 0.0,
                'temporal_coherence': 0.0,
                'resonance_strength': 0.0
            }

        # Compute aggregate metrics
        trsi_values = [w.trsi_value for w in windows]
        coherence_values = [w.coherence_score for w in windows]
        coupling_values = [w.coupling_strength for w in windows]

        return {
            'average_trsi': statistics.mean(trsi_values),
            'trsi_volatility': statistics.stdev(trsi_values) if len(trsi_values) > 1 else 0.0,
            'temporal_coherence': statistics.mean(coherence_values),
            'resonance_strength': statistics.mean(coupling_values),
            'window_count': len(windows),
            'total_entries_processed': len(entries)
        }

    def get_current_metrics(self) -> TemporalResonanceMetrics:
        """
        Get current temporal resonance metrics for monitoring.

        Returns:
            Complete metrics snapshot for Prometheus export
        """
        # Compute 24h trend
        now = datetime.utcnow()
        yesterday = now - timedelta(hours=24)

        recent_history = [
            (ts, val) for ts, val in self._trsi_history
            if ts >= yesterday
        ]

        if len(recent_history) >= 2:
            oldest_val = recent_history[0][1]
            newest_val = recent_history[-1][1]
            trsi_trend = newest_val - oldest_val
        else:
            trsi_trend = 0.0

        # Get latest analysis if available
        # This would be populated by periodic analysis calls
        avg_decay = 0.5  # Placeholder - would be computed from recent entries
        avg_coupling = 1.0  # Placeholder

        return TemporalResonanceMetrics(
            current_trsi=self._last_trsi,
            trsi_trend_24h=trsi_trend,
            average_decay_weight=avg_decay,
            average_coupling_strength=avg_coupling,
            temporal_coherence_score=0.5,  # Will be computed by schema validator
            last_updated=now,
            window_count=len(self._trsi_history),
            total_entries_processed=sum(len(h) for h in [self._trsi_history])  # Simplified
        )

    def reset_history(self):
        """Reset internal TRSI history (for testing/cleanup)."""
        self._trsi_history.clear()
        self._last_trsi = 0.5


# Global instance for system-wide resonance computation
temporal_resonance_engine = TemporalResonanceEngine()