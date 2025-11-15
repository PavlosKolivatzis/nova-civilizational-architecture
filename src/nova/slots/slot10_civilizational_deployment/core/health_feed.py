"""HealthFeed adapter contract for real-time slot health signals."""

from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Dict, Optional
from dataclasses import dataclass


@dataclass
class Slot8Health:
    """Slot 8 Memory Lock & IDS health signals."""
    integrity_score: float
    quarantine_active: bool
    recent_recoveries: Dict[str, float]  # {"success_rate_5m": 0.95}
    checksum_mismatch: bool = False
    tamper_evidence: bool = False


@dataclass
class Slot4Health:
    """Slot 4 TRI Engine health signals."""
    safe_mode_active: bool
    drift_z: float
    tri_score: Optional[float] = None


@dataclass
class RuntimeMetrics:
    """Current runtime performance metrics."""
    error_rate: float
    latency_p95: float
    saturation: float


class HealthFeedAdapter(ABC):
    """Abstract adapter for pulling live health signals from slots."""

    @abstractmethod
    def get_slot8_health(self) -> Slot8Health:
        """Get current Slot 8 Memory Lock & IDS health."""
        pass

    @abstractmethod
    def get_slot4_health(self) -> Slot4Health:
        """Get current Slot 4 TRI Engine health."""
        pass

    @abstractmethod
    def get_runtime_metrics(self) -> RuntimeMetrics:
        """Get current runtime performance metrics."""
        pass


class MockHealthFeed(HealthFeedAdapter):
    """Mock implementation for testing."""

    def __init__(self,
                 slot8_health: Optional[Slot8Health] = None,
                 slot4_health: Optional[Slot4Health] = None,
                 runtime_metrics: Optional[RuntimeMetrics] = None):
        self._slot8 = slot8_health or Slot8Health(
            integrity_score=0.95,
            quarantine_active=False,
            recent_recoveries={"success_rate_5m": 0.95}
        )
        self._slot4 = slot4_health or Slot4Health(
            safe_mode_active=False,
            drift_z=0.5,
            tri_score=0.75  # Mock value for testing
        )
        self._runtime = runtime_metrics or RuntimeMetrics(
            error_rate=0.01,
            latency_p95=100.0,
            saturation=0.30
        )

    def get_slot8_health(self) -> Slot8Health:
        return self._slot8

    def get_slot4_health(self) -> Slot4Health:
        return self._slot4

    def get_runtime_metrics(self) -> RuntimeMetrics:
        return self._runtime

    def update_slot8(self, **kwargs):
        """Update Slot 8 health for testing."""
        for key, value in kwargs.items():
            if hasattr(self._slot8, key):
                setattr(self._slot8, key, value)

    def update_slot4(self, **kwargs):
        """Update Slot 4 health for testing."""
        for key, value in kwargs.items():
            if hasattr(self._slot4, key):
                setattr(self._slot4, key, value)

    def update_runtime(self, **kwargs):
        """Update runtime metrics for testing."""
        for key, value in kwargs.items():
            if hasattr(self._runtime, key):
                setattr(self._runtime, key, value)


class LiveHealthFeed(HealthFeedAdapter):
    """Live implementation pulling from actual slot adapters."""

    def __init__(self, slot8_adapter=None, slot4_adapter=None, metrics_collector=None):
        # Import lazily to avoid circular dependencies
        self.slot8_adapter = slot8_adapter
        self.slot4_adapter = slot4_adapter
        self.metrics_collector = metrics_collector

    def get_slot8_health(self) -> Slot8Health:
        """Pull live Slot 8 health from memory lock system."""
        if not self.slot8_adapter:
            # Fallback to safe defaults if adapter not available
            return Slot8Health(
                integrity_score=0.95,
                quarantine_active=False,
                recent_recoveries={"success_rate_5m": 0.95}
            )

        try:
            # Get metrics from Slot 8 adapter
            metrics = self.slot8_adapter.get_health_metrics()
            return Slot8Health(
                integrity_score=metrics.get("integrity_score", 0.95),
                quarantine_active=metrics.get("quarantine_active", False),
                recent_recoveries=metrics.get("recent_recoveries", {"success_rate_5m": 0.95}),
                checksum_mismatch=metrics.get("checksum_mismatch", False),
                tamper_evidence=metrics.get("tamper_evidence", False)
            )
        except Exception:
            # Fallback on any error
            return Slot8Health(
                integrity_score=0.5,  # Conservative fallback
                quarantine_active=True,  # Safe default
                recent_recoveries={"success_rate_5m": 0.5}
            )

    def get_slot4_health(self) -> Slot4Health:
        """Pull live Slot 4 health from TRI engine."""
        if not self.slot4_adapter:
            return Slot4Health(safe_mode_active=False, drift_z=0.5, tri_score=None)

        try:
            metrics = self.slot4_adapter.get_health_metrics()

            # Get tri_score: prefer direct TRI engine, fall back to mirror, else None
            tri_score = None
            if hasattr(self.slot4_adapter, 'tri_engine') and self.slot4_adapter.tri_engine is not None:
                try:
                    health = self.slot4_adapter.tri_engine.assess()
                    tri_score = getattr(health, "tri_score", None)
                except Exception:
                    tri_score = None

            if tri_score is None and hasattr(self, 'mirror') and self.mirror is not None:
                try:
                    tri_score = self.mirror.read("slot04.tri_score", None)
                    if tri_score is not None:
                        tri_score = float(tri_score)
                except Exception:
                    tri_score = None

            return Slot4Health(
                safe_mode_active=metrics.get("safe_mode_active", False),
                drift_z=metrics.get("drift_z", 0.5),
                tri_score=tri_score
            )
        except Exception:
            # Safe defaults on error
            return Slot4Health(safe_mode_active=True, drift_z=999.0, tri_score=None)

    def get_runtime_metrics(self) -> RuntimeMetrics:
        """Pull live runtime performance metrics."""
        if not self.metrics_collector:
            return RuntimeMetrics(error_rate=0.01, latency_p95=100.0, saturation=0.30)

        try:
            metrics = self.metrics_collector.get_current_metrics()
            return RuntimeMetrics(
                error_rate=metrics.get("error_rate", 0.01),
                latency_p95=metrics.get("latency_p95", 100.0),
                saturation=metrics.get("saturation", 0.30)
            )
        except Exception:
            # Conservative defaults on error
            return RuntimeMetrics(error_rate=0.05, latency_p95=200.0, saturation=0.70)
