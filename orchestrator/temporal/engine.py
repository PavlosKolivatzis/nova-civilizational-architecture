"""Temporal engine implementation (Phase-6 readiness)."""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from statistics import mean
from typing import Any, Dict, List, Optional

try:  # pragma: no cover - semantic mirror optional
    from orchestrator.semantic_mirror import publish as mirror_publish
except Exception:  # pragma: no cover
    mirror_publish = None  # type: ignore[assignment]

from orchestrator.temporal.ledger import TemporalLedger
from orchestrator.temporal.metrics import record_temporal_metrics


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


@dataclass
class TemporalSnapshot:
    timestamp: float
    tri_coherence: float
    tri_drift_z: float
    slot07_mode: str
    gate_state: bool
    governance_state: str
    prediction_error: float
    temporal_drift: float
    temporal_variance: float
    convergence_score: float
    divergence_penalty: float
    raw: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "timestamp": self.timestamp,
            "tri_coherence": self.tri_coherence,
            "tri_drift_z": self.tri_drift_z,
            "slot07_mode": self.slot07_mode,
            "gate_state": self.gate_state,
            "governance_state": self.governance_state,
            "prediction_error": self.prediction_error,
            "temporal_drift": self.temporal_drift,
            "temporal_variance": self.temporal_variance,
            "convergence_score": self.convergence_score,
            "divergence_penalty": self.divergence_penalty,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TemporalSnapshot":
        """Construct a snapshot object from a semantic mirror payload."""
        return cls(
            timestamp=_safe_float(data.get("timestamp"), default=time.time()),
            tri_coherence=_safe_float(data.get("tri_coherence")),
            tri_drift_z=_safe_float(data.get("tri_drift_z")),
            slot07_mode=str(data.get("slot07_mode", "UNKNOWN")).upper(),
            gate_state=bool(data.get("gate_state", True)),
            governance_state=str(data.get("governance_state", "ok")),
            prediction_error=_safe_float(data.get("prediction_error")),
            temporal_drift=_safe_float(data.get("temporal_drift")),
            temporal_variance=_safe_float(data.get("temporal_variance")),
            convergence_score=_safe_float(data.get("convergence_score"), default=1.0),
            divergence_penalty=_safe_float(data.get("divergence_penalty")),
            raw=dict(data),
        )


class TemporalEngine:
    """Temporal core computation leveraging the temporal ledger."""

    def __init__(self, ledger: TemporalLedger):
        self._ledger = ledger

    def _recent_coherences(self, limit: int = 5) -> List[float]:
        values: List[float] = []
        for entry in self._ledger.snapshot():
            coherence = entry["entry"].get("tri_coherence")
            if coherence is not None:
                values.append(float(coherence))
        return values[-limit:]

    def compute(self, payload: Dict[str, Any]) -> TemporalSnapshot:
        timestamp = _safe_float(payload.get("timestamp"), default=time.time())
        tri_signal = payload.get("tri_signal", {})
        tri_coherence = _safe_float(tri_signal.get("tri_coherence"))
        tri_drift_z = _safe_float(tri_signal.get("tri_drift_z"))

        slot07 = payload.get("slot07", {})
        slot07_mode = str(slot07.get("mode", "UNKNOWN")).upper()

        slot10 = payload.get("slot10", {})
        gate_state = bool(slot10.get("passed", True))

        governance = payload.get("governance", {})
        governance_state = str(governance.get("state", governance.get("reason", "ok")))

        prev_entry = self._ledger.head()
        prev_data = prev_entry["entry"] if prev_entry else {}
        prev_coherence = _safe_float(prev_data.get("tri_coherence"), default=tri_coherence)

        temporal_drift = abs(tri_coherence - prev_coherence)

        history = self._recent_coherences()
        history.append(tri_coherence)
        if len(history) > 1:
            avg = mean(history)
            temporal_variance = mean((value - avg) ** 2 for value in history)
        else:
            temporal_variance = 0.0

        prediction_target = _safe_float(payload.get("prediction"), default=tri_coherence)
        prediction_error = abs(tri_coherence - prediction_target)

        convergence_score = max(0.0, 1.0 - min(1.0, temporal_drift))
        divergence_penalty = min(1.0, temporal_variance + prediction_error)

        snapshot = TemporalSnapshot(
            timestamp=timestamp,
            tri_coherence=tri_coherence,
            tri_drift_z=tri_drift_z,
            slot07_mode=slot07_mode,
            gate_state=gate_state,
            governance_state=governance_state,
            prediction_error=prediction_error,
            temporal_drift=temporal_drift,
            temporal_variance=temporal_variance,
            convergence_score=convergence_score,
            divergence_penalty=divergence_penalty,
            raw=dict(payload),
        )

        self._ledger.append(snapshot.to_dict())
        record_temporal_metrics(snapshot)
        self._publish_snapshot(snapshot)
        return snapshot

    def _publish_snapshot(self, snapshot: TemporalSnapshot) -> None:
        if not mirror_publish:
            return
        try:
            mirror_publish("temporal.snapshot", snapshot.to_dict(), "temporal", ttl=300.0)
            head = self._ledger.head()
            if head:
                mirror_publish("temporal.ledger_head", head, "temporal", ttl=300.0)
        except Exception:
            return
