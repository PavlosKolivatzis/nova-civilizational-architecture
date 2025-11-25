"""
Phase 10: Meta-Stability Engine (MSE)

Detects instability of stability itself by monitoring variance in URF composite_risk.
High variance indicates oscillatory or runaway feedback patterns.

Contract: contracts/mse@1.yaml
"""

from __future__ import annotations

import statistics
from collections import deque
from datetime import datetime, timezone
from typing import Dict, List, Optional


def _clamp(val: float, min_val: float = 0.0, max_val: float = 1.0) -> float:
    """Clamp value to [min_val, max_val]."""
    return max(min_val, min(max_val, val))


class MetaStabilityEngine:
    """
    Meta-Stability Engine: Monitors variance in URF composite_risk over time.

    Detects three states:
    - stable: variance < 0.05 (low fluctuation)
    - oscillating: 0.05 ≤ variance < 0.15 (moderate fluctuation)
    - runaway: variance ≥ 0.15 (high fluctuation, feedback loop)
    """

    def __init__(
        self,
        window_size: int = 10,
        stable_threshold: float = 0.05,
        oscillating_threshold: float = 0.15,
    ):
        """
        Initialize MSE.

        Args:
            window_size: Number of recent samples for variance calculation
            stable_threshold: Variance threshold for stable state
            oscillating_threshold: Variance threshold for runaway state
        """
        self.window_size = window_size
        self.stable_threshold = stable_threshold
        self.oscillating_threshold = oscillating_threshold

        self._samples: deque[float] = deque(maxlen=window_size)
        self._timestamps: deque[str] = deque(maxlen=window_size)
        self._previous_instability: Optional[float] = None
        self._previous_timestamp: Optional[datetime] = None

    def add_sample(self, composite_risk: float, timestamp: Optional[str] = None) -> None:
        """
        Add a new composite_risk sample.

        Args:
            composite_risk: URF composite_risk value [0.0, 1.0]
            timestamp: ISO 8601 timestamp (defaults to now)
        """
        clamped = _clamp(composite_risk)
        ts = timestamp or datetime.now(timezone.utc).isoformat()

        self._samples.append(clamped)
        self._timestamps.append(ts)

    def compute_meta_instability(self) -> Dict:
        """
        Compute meta-instability from current sample window.

        Returns:
            Dict with:
                - meta_instability: float [0.0, 1.0]
                - trend: str ("stable" | "oscillating" | "runaway")
                - samples: List[float]
                - window_size: int
                - drift_velocity: float
                - timestamp: str
        """
        if len(self._samples) < 2:
            # Not enough samples for variance
            return {
                "meta_instability": 0.0,
                "trend": "stable",
                "samples": list(self._samples),
                "sample_count": len(self._samples),
                "window_size": self.window_size,
                "drift_velocity": 0.0,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }

        # Compute variance
        variance = statistics.variance(self._samples)
        meta_instability = _clamp(variance)

        # Classify trend
        if meta_instability < self.stable_threshold:
            trend = "stable"
        elif meta_instability < self.oscillating_threshold:
            trend = "oscillating"
        else:
            trend = "runaway"

        # Compute drift velocity (rate of change)
        drift_velocity = 0.0
        if self._previous_instability is not None and self._previous_timestamp is not None:
            current_time = datetime.fromisoformat(self._timestamps[-1].replace("Z", "+00:00"))
            time_delta = (current_time - self._previous_timestamp).total_seconds()
            if time_delta > 0:
                drift_velocity = (meta_instability - self._previous_instability) / time_delta

        # Update state
        self._previous_instability = meta_instability
        if self._timestamps:
            self._previous_timestamp = datetime.fromisoformat(
                self._timestamps[-1].replace("Z", "+00:00")
            )

        return {
            "meta_instability": meta_instability,
            "trend": trend,
            "samples": list(self._samples),
            "sample_count": len(self._samples),
            "window_size": self.window_size,
            "drift_velocity": drift_velocity,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    def get_snapshot(self) -> Dict:
        """
        Get current MSE snapshot without computing new variance.

        Returns:
            Dict with current state
        """
        return self.compute_meta_instability()

    def reset(self) -> None:
        """Clear all samples and reset state."""
        self._samples.clear()
        self._timestamps.clear()
        self._previous_instability = None
        self._previous_timestamp = None


# Global MSE instance for runtime use
_MSE_ENGINE: Optional[MetaStabilityEngine] = None


def get_mse_engine(
    window_size: int = 10,
    stable_threshold: float = 0.05,
    oscillating_threshold: float = 0.15,
) -> MetaStabilityEngine:
    """
    Get or create global MSE engine instance.

    Args:
        window_size: Sample window size
        stable_threshold: Stable state threshold
        oscillating_threshold: Oscillating state threshold

    Returns:
        MetaStabilityEngine instance
    """
    global _MSE_ENGINE
    if _MSE_ENGINE is None:
        _MSE_ENGINE = MetaStabilityEngine(
            window_size=window_size,
            stable_threshold=stable_threshold,
            oscillating_threshold=oscillating_threshold,
        )
    return _MSE_ENGINE


def record_composite_risk_sample(composite_risk: float) -> None:
    """
    Record a composite_risk sample to the MSE engine.

    Args:
        composite_risk: URF composite_risk value [0.0, 1.0]
    """
    engine = get_mse_engine()
    engine.add_sample(composite_risk)


def get_meta_stability_snapshot() -> Dict:
    """
    Get current meta-stability snapshot from global engine.

    Returns:
        Dict with MSE metrics
    """
    engine = get_mse_engine()
    return engine.get_snapshot()


def compute_router_penalty(meta_instability: float) -> float:
    """
    Compute router penalty based on meta-instability.

    Args:
        meta_instability: MSE meta_instability value [0.0, 1.0]

    Returns:
        Penalty value [0.0, 0.5]
    """
    penalty_start = 0.08
    penalty_max = 0.5
    cooldown_multiplier = 2.0

    if meta_instability < penalty_start:
        return 0.0

    penalty = (meta_instability - penalty_start) * cooldown_multiplier
    return min(penalty_max, penalty)


def should_block_governance(meta_instability: float, threshold: float = 0.15) -> bool:
    """
    Check if governance should block based on meta-instability.

    Args:
        meta_instability: MSE meta_instability value
        threshold: Block threshold (default 0.15)

    Returns:
        True if should block
    """
    return meta_instability >= threshold


def should_block_deployment(meta_instability: float, threshold: float = 0.12) -> bool:
    """
    Check if Slot10 should block deployment based on meta-instability.

    Args:
        meta_instability: MSE meta_instability value
        threshold: Block threshold (default 0.12)

    Returns:
        True if should block
    """
    return meta_instability >= threshold
