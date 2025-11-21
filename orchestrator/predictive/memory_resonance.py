"""
Memory Resonance Service — Phase 7.0-RC

Tracks 7-day rolling TRSI history for long-term stability analysis.
Implements memory stability scoring (mean - stdev) and trend detection.

Read-only observer - does not mutate system state.
"""

from __future__ import annotations

import statistics
import time
from collections import deque
from dataclasses import dataclass
from typing import Optional

try:  # pragma: no cover - semantic mirror optional
    from orchestrator.semantic_mirror import publish as mirror_publish
except Exception:  # pragma: no cover
    mirror_publish = None  # type: ignore[assignment]


@dataclass
class TRSISample:
    """Single TRSI sample with timestamp and source tracking."""
    timestamp: float
    trsi_value: float
    source: str = "temporal_engine"  # or "predictive_engine"


class MemoryResonanceWindow:
    """
    Rolling 7-day TRSI stability memory.

    Maintains hourly TRSI samples in a fixed-size deque (168 samples = 7 days × 24 hours).
    Computes memory stability as: mean(TRSI) - stdev(TRSI)

    Usage:
        window = MemoryResonanceWindow()
        window.add_sample(trsi_value=0.85, timestamp=time.time())
        stability = window.compute_memory_stability()  # Returns float [0.0, 1.0]
    """

    def __init__(self, window_days: int = 7):
        """
        Initialize memory window.

        Args:
            window_days: Number of days to track (default: 7 for RC validation)
        """
        self.window_days = window_days
        self.window_hours = window_days * 24
        self.trsi_history: deque[TRSISample] = deque(maxlen=self.window_hours)

    def add_sample(
        self,
        trsi_value: float,
        timestamp: Optional[float] = None,
        source: str = "temporal_engine"
    ) -> None:
        """
        Add TRSI sample to rolling window.

        Args:
            trsi_value: TRSI value [0.0, 1.0]
            timestamp: Unix timestamp (defaults to current time)
            source: Source identifier for tracking ("temporal_engine", "predictive_engine")
        """
        if timestamp is None:
            timestamp = time.time()

        # Validate inputs
        trsi_value = max(0.0, min(1.0, float(trsi_value)))

        sample = TRSISample(
            timestamp=timestamp,
            trsi_value=trsi_value,
            source=source
        )
        self.trsi_history.append(sample)

    def compute_memory_stability(self) -> float:
        """
        Compute long-term stability score from rolling window.

        Formula (Phase 7.0-RC blueprint):
            stability = mean(TRSI) - stdev(TRSI)

        Returns:
            float: Stability score [0.0, 1.0]
                - 0.5 if insufficient data (<24 hours)
                - Clamped to [0.0, 1.0] range
        """
        if len(self.trsi_history) < 24:  # Need at least 1 day
            return 0.5  # Neutral baseline

        values = [sample.trsi_value for sample in self.trsi_history]
        mean_trsi = statistics.mean(values)
        volatility = statistics.stdev(values) if len(values) > 1 else 0.0

        # Stability penalizes volatility (conservative approach)
        stability = mean_trsi - volatility
        return max(0.0, min(1.0, stability))

    def get_trend(self, hours: int = 24) -> float:
        """
        Compute TRSI trend over last N hours.

        Args:
            hours: Lookback period in hours (default: 24)

        Returns:
            float: Trend (delta between oldest and newest in window)
                - Positive: improving
                - Negative: degrading
                - 0.0: insufficient data
        """
        if len(self.trsi_history) < 2:
            return 0.0

        cutoff_time = time.time() - (hours * 3600)
        recent = [s for s in self.trsi_history if s.timestamp >= cutoff_time]

        if len(recent) < 2:
            return 0.0

        return recent[-1].trsi_value - recent[0].trsi_value

    def get_window_stats(self) -> dict:
        """
        Get comprehensive window statistics.

        Returns:
            dict: Statistics including:
                - count: Number of samples
                - mean: Average TRSI
                - stdev: Standard deviation
                - min/max: Range
                - stability: Memory stability score
                - trend_24h: 24-hour trend
                - window_start/end: Timestamp bounds
        """
        if not self.trsi_history:
            return {
                "count": 0,
                "mean": 0.5,
                "stdev": 0.0,
                "min": 0.0,
                "max": 0.0,
                "stability": 0.5,
                "trend_24h": 0.0,
                "window_start": None,
                "window_end": None,
            }

        values = [s.trsi_value for s in self.trsi_history]

        return {
            "count": len(values),
            "mean": statistics.mean(values),
            "stdev": statistics.stdev(values) if len(values) > 1 else 0.0,
            "min": min(values),
            "max": max(values),
            "stability": self.compute_memory_stability(),
            "trend_24h": self.get_trend(24),
            "window_start": self.trsi_history[0].timestamp,
            "window_end": self.trsi_history[-1].timestamp,
        }

    def to_dict(self) -> dict:
        """
        Serialize window state to dict for semantic mirror publishing.

        Returns:
            dict: Serialized window with stats
        """
        stats = self.get_window_stats()
        return {
            "window_days": self.window_days,
            "window_hours": self.window_hours,
            "samples": stats["count"],
            "memory_stability": stats["stability"],
            "mean_trsi": stats["mean"],
            "volatility": stats["stdev"],
            "trend_24h": stats["trend_24h"],
            "window_start": stats["window_start"],
            "window_end": stats["window_end"],
            "timestamp": time.time(),
        }

    def publish_to_mirror(self, ttl: float = 300.0) -> None:
        """
        Publish memory resonance state to semantic mirror and Prometheus.

        Args:
            ttl: Time-to-live in seconds (default: 300 = 5 minutes)
        """
        # Publish to semantic mirror
        if mirror_publish:
            try:
                mirror_publish(
                    "predictive.memory_resonance",
                    self.to_dict(),
                    "governance",
                    ttl=ttl
                )
            except Exception:  # pragma: no cover
                pass  # Fail silently (observability, not critical path)

        # Record Prometheus metrics (Phase 7.0-RC Step 5)
        try:
            from orchestrator.prometheus_metrics import record_memory_resonance
            stats = self.get_window_stats()
            record_memory_resonance(stats)
        except Exception:  # pragma: no cover
            pass  # Fail silently


# Singleton instance for system-wide memory tracking
_memory_window_instance: Optional[MemoryResonanceWindow] = None


def get_memory_window() -> MemoryResonanceWindow:
    """
    Get or create singleton memory resonance window.

    Returns:
        MemoryResonanceWindow: Global memory window instance
    """
    global _memory_window_instance
    if _memory_window_instance is None:
        _memory_window_instance = MemoryResonanceWindow()
    return _memory_window_instance


def reset_memory_window() -> None:
    """
    Reset singleton memory window (for testing).

    Clears all history and reinitializes window.
    """
    global _memory_window_instance
    _memory_window_instance = MemoryResonanceWindow()
