from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict

from orchestrator.temporal.engine import TemporalEngine
from orchestrator.temporal.ledger import TemporalLedger
from orchestrator.thresholds.manager import snapshot_thresholds


@dataclass
class TemporalConstraintResult:
    allowed: bool
    reason: str = "ok"
    snapshot: Dict[str, Any] | None = None
    penalty: float = 0.0

    def to_dict(self):
        return {
            "allowed": self.allowed,
            "reason": self.reason,
            "snapshot": self.snapshot or {},
            "penalty": self.penalty,
        }


class TemporalConstraintEngine:
    """Evaluate temporal constraints before routing decisions."""

    def __init__(self, ledger: TemporalLedger | None = None):
        self._ledger = ledger or TemporalLedger()
        self._engine = TemporalEngine(self._ledger)

    def evaluate(self, payload: Dict[str, Any]) -> TemporalConstraintResult:
        thresholds = snapshot_thresholds()
        temporal_threshold = thresholds.get("temporal_drift_threshold", 0.3)
        variance_threshold = thresholds.get("temporal_variance_threshold", 0.1)
        prediction_threshold = thresholds.get("temporal_prediction_error_threshold", 0.2)
        min_coherence = thresholds.get("min_temporal_coherence", 0.7)

        tri_signal = payload.get("tri_signal") or {}
        if "tri_coherence" not in tri_signal:
            return TemporalConstraintResult(
                allowed=True,
                reason="temporal_data_missing",
                snapshot={"tri_signal": tri_signal},
            )

        snapshot = self._engine.compute(payload)
        allowed = True
        reason = "ok"
        penalty = 0.0

        if snapshot.tri_coherence < min_coherence:
            allowed = False
            reason = "temporal_coherence_low"
        elif snapshot.temporal_drift > temporal_threshold:
            allowed = False
            reason = "temporal_drift_high"
        elif snapshot.temporal_variance > variance_threshold:
            penalty = min(1.0, snapshot.temporal_variance)
        elif snapshot.prediction_error > prediction_threshold:
            penalty = min(1.0, snapshot.prediction_error)

        return TemporalConstraintResult(
            allowed=allowed,
            reason=reason,
            snapshot=snapshot.to_dict(),
            penalty=penalty,
        )
