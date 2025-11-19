"""
Centralized threshold management for slots interacting with wisdom governor & cultural synthesis.

Responsibilities:
- Maintain default threshold values.
- Apply environment overrides (NOVA_SLOT07_TRI_DRIFT_THRESHOLD, etc.).
- Optionally incorporate TRI truth signal metadata to adjust effective thresholds.
- Publish Prometheus gauges so operators can see current values.
- Provide a lightweight snapshot for debugging/tests.
"""

from __future__ import annotations

import os
import threading
from dataclasses import dataclass, asdict
from typing import Dict, Optional

from prometheus_client import Gauge
from nova.metrics.registry import REGISTRY as INTERNAL_REGISTRY

THRESHOLD_GAUGE = Gauge(
    "nova_threshold_value",
    "Configured thresholds for wisdom governor and cultural synthesis",
    ["name"],
    registry=INTERNAL_REGISTRY,
)


def _env_float(name: str, default: float) -> float:
    value = os.getenv(name)
    if value is None:
        return default
    try:
        return float(value)
    except ValueError:
        return default


@dataclass(frozen=True)
class Slot7Thresholds:
    drift_threshold: float = 2.2
    stability_threshold: float = 0.03
    stability_threshold_tri: float = 0.05
    effective_stability_threshold: float = 0.03


@dataclass(frozen=True)
class Slot6Thresholds:
    tri_min_score: float = 0.8


@dataclass(frozen=True)
class ThresholdSnapshot:
    slot7: Slot7Thresholds
    slot6: Slot6Thresholds
    tri_signal: Optional[Dict[str, float]]


class ThresholdManager:
    """Manage thresholds with env overrides and TRI enrichment."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._slot7 = self._load_slot7()
        self._slot6 = self._load_slot6()
        self._last_tri_signal: Optional[Dict[str, float]] = None
        self._publish_metrics()

    # ------------------------------------------------------------------
    # Loaders
    # ------------------------------------------------------------------
    def _load_slot7(self) -> Slot7Thresholds:
        drift = _env_float("NOVA_SLOT07_TRI_DRIFT_THRESHOLD", 2.2)
        stab = _env_float("NOVA_SLOT07_STABILITY_THRESHOLD", 0.03)
        stab_tri = _env_float("NOVA_SLOT07_STABILITY_THRESHOLD_TRI", 0.05)
        return Slot7Thresholds(
            drift_threshold=drift,
            stability_threshold=stab,
            stability_threshold_tri=stab_tri,
            effective_stability_threshold=stab,
        )

    def _load_slot6(self) -> Slot6Thresholds:
        tri_min = _env_float("NOVA_SLOT06_TRI_MIN_SCORE", 0.8)
        return Slot6Thresholds(tri_min_score=tri_min)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def refresh_from_env(self) -> None:
        with self._lock:
            self._slot7 = self._load_slot7()
            self._slot6 = self._load_slot6()
            self._slot7 = self._apply_tri_to_slot7(self._slot7, self._last_tri_signal)
            self._publish_metrics()

    def update_from_tri_signal(self, signal: Dict[str, float]) -> None:
        """Store latest TRI signal (tri_truth_signal@1 semantics)."""
        sanitized = {
            "tri_coherence": float(signal.get("tri_coherence", 0.0) or 0.0),
            "tri_drift_z": float(signal.get("tri_drift_z", 0.0) or 0.0),
            "tri_band": str(signal.get("tri_band", "")).lower(),
        }
        with self._lock:
            self._last_tri_signal = sanitized
            self._slot7 = self._apply_tri_to_slot7(self._slot7, sanitized)
            self._publish_metrics()

    def get_slot7_thresholds(self) -> Slot7Thresholds:
        with self._lock:
            return self._slot7

    def get_slot6_thresholds(self) -> Slot6Thresholds:
        with self._lock:
            return self._slot6

    def snapshot(self) -> ThresholdSnapshot:
        with self._lock:
            return ThresholdSnapshot(
                slot7=self._slot7,
                slot6=self._slot6,
                tri_signal=dict(self._last_tri_signal) if self._last_tri_signal else None,
            )

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------
    def _apply_tri_to_slot7(
        self,
        slot7: Slot7Thresholds,
        tri_signal: Optional[Dict[str, float]],
    ) -> Slot7Thresholds:
        effective = slot7.stability_threshold
        if tri_signal:
            band = tri_signal.get("tri_band", "")
            drift = tri_signal.get("tri_drift_z", 0.0)
            if band == "red" or (isinstance(drift, float) and drift >= slot7.drift_threshold):
                effective = slot7.stability_threshold_tri
        return Slot7Thresholds(
            drift_threshold=slot7.drift_threshold,
            stability_threshold=slot7.stability_threshold,
            stability_threshold_tri=slot7.stability_threshold_tri,
            effective_stability_threshold=effective,
        )

    def _publish_metrics(self) -> None:
        THRESHOLD_GAUGE.labels(name="slot07_drift_threshold").set(self._slot7.drift_threshold)
        THRESHOLD_GAUGE.labels(name="slot07_stability_threshold").set(self._slot7.stability_threshold)
        THRESHOLD_GAUGE.labels(name="slot07_stability_threshold_tri").set(self._slot7.stability_threshold_tri)
        THRESHOLD_GAUGE.labels(name="slot07_effective_stability_threshold").set(
            self._slot7.effective_stability_threshold
        )
        THRESHOLD_GAUGE.labels(name="slot06_tri_min_score").set(self._slot6.tri_min_score)


_MANAGER: Optional[ThresholdManager] = None


def get_threshold_manager() -> ThresholdManager:
    global _MANAGER
    if _MANAGER is None:
        _MANAGER = ThresholdManager()
    return _MANAGER


def reset_threshold_manager_for_tests() -> None:
    """Reset singleton for deterministic tests."""
    global _MANAGER
    _MANAGER = None
