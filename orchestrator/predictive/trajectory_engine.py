"""Predictive Trajectory Engine (Phase-7 scaffold)."""

from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Any, Dict, Optional

from orchestrator.temporal.engine import TemporalSnapshot
from orchestrator.thresholds import get_threshold
from orchestrator.predictive.ledger import PredictiveLedger

try:  # pragma: no cover - semantic mirror optional in tests
    from orchestrator.semantic_mirror import publish as mirror_publish
except Exception:  # pragma: no cover
    mirror_publish = None  # type: ignore[assignment]


def _safe_threshold(name: str, default: float) -> float:
    try:
        value = get_threshold(name)
    except Exception:
        return default
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


@dataclass
class PredictiveSnapshot:
    drift_velocity: float
    drift_acceleration: float
    stability_pressure: float
    collapse_risk: float
    safe_corridor: bool
    timestamp: float
    raw: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PredictiveSnapshot":
        return cls(
            drift_velocity=float(data.get("drift_velocity", 0.0)),
            drift_acceleration=float(data.get("drift_acceleration", 0.0)),
            stability_pressure=float(data.get("stability_pressure", 0.0)),
            collapse_risk=float(data.get("collapse_risk", 0.0)),
            safe_corridor=bool(data.get("safe_corridor", False)),
            timestamp=float(data.get("timestamp", 0.0)),
            raw=dict(data),
        )


class PredictiveTrajectoryEngine:
    """Deterministic predictor built on temporal snapshots."""

    def __init__(self, ledger: PredictiveLedger | None = None, horizon_seconds: float = 60.0):
        self._last_snapshot: Optional[TemporalSnapshot] = None
        self._last_velocity: float = 0.0
        self._ledger = ledger or PredictiveLedger()
        self._horizon_seconds = float(horizon_seconds)

    def predict(self, temporal: TemporalSnapshot) -> PredictiveSnapshot:
        prev_snapshot = self._last_snapshot
        dt = self._delta_time(prev_snapshot, temporal)
        previous_drift = prev_snapshot.tri_drift_z if prev_snapshot else temporal.tri_drift_z
        velocity = (temporal.tri_drift_z - previous_drift) / dt
        acceleration = (velocity - self._last_velocity) / dt if prev_snapshot else 0.0

        stability_pressure = self._stability_pressure(temporal)
        collapse_risk = self._collapse_risk(temporal, acceleration, stability_pressure)
        safe_corridor = self._is_safe_corridor(temporal, collapse_risk, acceleration)

        snapshot = PredictiveSnapshot(
            drift_velocity=velocity,
            drift_acceleration=acceleration,
            stability_pressure=stability_pressure,
            collapse_risk=collapse_risk,
            safe_corridor=safe_corridor,
            timestamp=temporal.timestamp,
            raw={
                "temporal": temporal.to_dict(),
                "previous_timestamp": prev_snapshot.timestamp if prev_snapshot else None,
            },
        )

        self._last_snapshot = temporal
        self._last_velocity = velocity
        self._append_to_ledger(snapshot, temporal)
        self._publish_snapshot(snapshot)
        return snapshot

    @staticmethod
    def _delta_time(previous: Optional[TemporalSnapshot], current: TemporalSnapshot) -> float:
        if previous is None:
            return 1.0
        dt = current.timestamp - previous.timestamp
        return 1.0 if dt <= 0 else dt

    def _stability_pressure(self, temporal: TemporalSnapshot) -> float:
        variance_threshold = max(_safe_threshold("temporal_variance_threshold", 0.1), 1e-6)
        pressure = max(0.0, temporal.temporal_variance / variance_threshold)
        if temporal.slot07_mode.upper() == "FROZEN":
            pressure += 1.0
        if not temporal.gate_state:
            pressure += 0.5
        return pressure

    def _collapse_risk(
        self,
        temporal: TemporalSnapshot,
        acceleration: float,
        stability_pressure: float,
    ) -> float:
        drift_threshold = max(_safe_threshold("temporal_drift_threshold", 0.3), 1e-6)
        prediction_threshold = max(_safe_threshold("temporal_prediction_error_threshold", 0.2), 1e-6)

        accel_component = abs(acceleration) / drift_threshold
        prediction_component = max(0.0, temporal.prediction_error) / prediction_threshold
        pressure_component = stability_pressure * 0.25

        return min(1.0, accel_component + prediction_component + pressure_component)

    def _is_safe_corridor(
        self,
        temporal: TemporalSnapshot,
        collapse_risk: float,
        acceleration: float,
    ) -> bool:
        coherence_threshold = _safe_threshold("min_temporal_coherence", 0.7)
        variance_threshold = _safe_threshold("temporal_variance_threshold", 0.1)
        return (
            temporal.tri_coherence >= coherence_threshold
            and abs(acceleration) <= variance_threshold
            and collapse_risk < 0.5
        )

    def _publish_snapshot(self, snapshot: PredictiveSnapshot) -> None:
        if not mirror_publish:
            return
        try:  # pragma: no cover - mirror publishing optional
            mirror_publish(
                "predictive.prediction_snapshot",
                snapshot.to_dict(),
                "predictive",
                ttl=180.0,
            )
        except Exception:
            return

    def _append_to_ledger(self, snapshot: PredictiveSnapshot, temporal: TemporalSnapshot) -> None:
        payload = {
            "timestamp": snapshot.timestamp,
            "horizon_seconds": self._horizon_seconds,
            "tri_coherence": temporal.tri_coherence,
            "drift_velocity": snapshot.drift_velocity,
            "drift_acceleration": snapshot.drift_acceleration,
            "stability_pressure": snapshot.stability_pressure,
            "predictive_collapse_risk": snapshot.collapse_risk,
            "predictive_safe_corridor": snapshot.safe_corridor,
            "source_snapshot_hash": temporal.raw.get("hash", "") if isinstance(temporal.raw, dict) else "",
            "metadata": {
                "slot07_mode": temporal.slot07_mode,
                "gate_state": temporal.gate_state,
                "governance_state": temporal.governance_state,
            },
        }
        try:
            self._ledger.append(payload)
            if mirror_publish:
                try:  # pragma: no cover - optional publish
                    mirror_publish("predictive.ledger_head", payload, "predictive", ttl=300.0)
                except Exception:
                    pass
        except Exception:
            return
