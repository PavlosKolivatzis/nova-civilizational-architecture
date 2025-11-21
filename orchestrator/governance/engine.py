from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field
from typing import Any, Deque, Dict, List, Optional

try:
    from orchestrator.semantic_mirror import publish as mirror_publish
except Exception:  # pragma: no cover
    mirror_publish = None  # type: ignore[assignment]

from orchestrator.governance.ethics import EthicsCheck, evaluate_ethics
from orchestrator.governance.state_ledger import GovernanceLedger
from orchestrator.prometheus.governance_metrics import record_governance_result
from orchestrator.router.constraints import _tri_signal_from_request as _tri_signal  # type: ignore
from orchestrator.router.constraints import _slot07_state as _slot07_state  # type: ignore
from orchestrator.router.constraints import _slot10_state as _slot10_state  # type: ignore
from orchestrator.router.constraints import _current_thresholds as _current_thresholds  # type: ignore
from orchestrator.temporal.ledger import TemporalLedger
from orchestrator.temporal.engine import TemporalEngine, TemporalSnapshot
from orchestrator.temporal.adapters import (
    read_temporal_snapshot,
    read_temporal_router_modifiers,
    read_temporal_ledger_head,
)
from orchestrator.predictive.trajectory_engine import PredictiveTrajectoryEngine, PredictiveSnapshot
from orchestrator.predictive.adapters import (
    read_predictive_snapshot,
    read_predictive_ledger_head,
)

try:  # pragma: no cover - metrics optional
    from orchestrator.prometheus_metrics import record_predictive_warning
except Exception:  # pragma: no cover
    def record_predictive_warning(reason: str | None = None) -> None:  # type: ignore[misc]
        return


@dataclass
class GovernanceResult:
    allowed: bool
    reason: str
    ethics: List[EthicsCheck] = field(default_factory=list)
    snapshot: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "allowed": self.allowed,
            "reason": self.reason,
            "ethics": [check.to_dict() for check in self.ethics],
            "snapshot": self.snapshot,
            "metadata": self.metadata,
        }


class GovernanceEngine:
    """Enforces system-wide governance rules and ethical invariants."""

    def __init__(
        self,
        ledger: Optional[GovernanceLedger] = None,
        temporal_ledger: Optional[TemporalLedger] = None,
        predictive_engine: Optional[PredictiveTrajectoryEngine] = None,
        predictive_history_window: int = 5,
    ):
        self._ledger = ledger or GovernanceLedger()
        self._temporal_engine = TemporalEngine(temporal_ledger or TemporalLedger())
        self._predictive_engine = predictive_engine or PredictiveTrajectoryEngine()
        self._predictive_history_window = max(1, int(predictive_history_window))
        self._predictive_history: Deque[Dict[str, Any]] = deque(maxlen=self._predictive_history_window)
        self._last_result: Optional[GovernanceResult] = None

    def evaluate(
        self,
        state: Optional[Dict[str, Any]] = None,
        routing_decision: Optional[Dict[str, Any]] = None,
        record: bool = True,
    ) -> GovernanceResult:
        state = dict(state or {})
        thresholds = _current_thresholds()
        tri_signal = state.get("tri_signal") or _tri_signal(state)
        slot07 = state.get("slot07") or _slot07_state(state)
        slot10 = state.get("slot10") or _slot10_state(state)

        existing_temporal = read_temporal_snapshot("governance")
        if existing_temporal:
            temporal_snapshot = TemporalSnapshot.from_dict(existing_temporal)
            temporal_payload = dict(existing_temporal)
        else:
            temporal_snapshot = self._temporal_engine.compute(state)
            temporal_payload = temporal_snapshot.to_dict()

        predictive_payload = read_predictive_snapshot("governance")
        if predictive_payload:
            predictive_snapshot = PredictiveSnapshot.from_dict(predictive_payload)
        else:
            predictive_obj = self._predictive_engine.predict(temporal_snapshot)
            predictive_snapshot = predictive_obj
            predictive_payload = predictive_obj.to_dict()

        history_window = max(1, int(thresholds.get("predictive_history_window", self._predictive_history_window)))
        if history_window != self._predictive_history_window:
            self._predictive_history = deque(list(self._predictive_history), maxlen=history_window)
            self._predictive_history_window = history_window

        self._predictive_history.append(dict(predictive_payload))

        snapshot = {
            "tri_signal": tri_signal,
            "slot07": slot07,
            "slot10": slot10,
            "thresholds": thresholds,
            "temporal": temporal_payload,
            "predictive": predictive_payload,
            "predictive_history": list(self._predictive_history),
        }
        ledger_head = read_temporal_ledger_head("governance")
        if ledger_head:
            snapshot["temporal_ledger_head"] = ledger_head
        router_modifiers = read_temporal_router_modifiers("governance")
        if router_modifiers:
            snapshot["temporal_router_modifiers"] = router_modifiers
        predictive_ledger_head = read_predictive_ledger_head("governance")
        if predictive_ledger_head:
            snapshot["predictive_ledger_head"] = predictive_ledger_head

        if routing_decision:
            snapshot["routing_decision"] = routing_decision

        ethics = evaluate_ethics(state)
        allowed = True
        reason = "ok"

        tri_coherence = tri_signal.get("tri_coherence")
        tri_drift = tri_signal.get("tri_drift_z")
        tri_jitter = tri_signal.get("tri_jitter")

        min_coherence = thresholds.get("tri_min_coherence", 0.65)
        drift_threshold = thresholds.get("slot07_tri_drift_threshold", 2.2)
        jitter_threshold = thresholds.get("tri_max_jitter", 0.30)

        if tri_coherence is not None and float(tri_coherence) < float(min_coherence):
            allowed = False
            reason = "tri_low"
        elif tri_drift is not None and abs(float(tri_drift)) > float(drift_threshold):
            allowed = False
            reason = "tri_drift_high"
        elif tri_jitter is not None and float(tri_jitter) > float(jitter_threshold):
            allowed = False
            reason = "tri_jitter_high"
        elif str(slot07.get("mode", "")).upper() == "FROZEN":
            allowed = False
            reason = "slot07_frozen"
        elif slot10 and not bool(slot10.get("passed", True)):
            allowed = False
            reason = str(slot10.get("reason", "slot10_gate_fail"))

        if allowed:
            for check in ethics:
                if not check.passed:
                    allowed = False
                    reason = check.rule
                    break

        metadata = {
            "stability_score": float(state.get("stability_score", 1.0) or 1.0),
            "policy_score": float(state.get("policy_score", 0.0) or 0.0),
            "temporal_convergence": temporal_snapshot.convergence_score,
            "temporal_penalty": temporal_snapshot.divergence_penalty,
            "predictive_collapse_risk": predictive_snapshot.collapse_risk,
            "predictive_safe_corridor": predictive_snapshot.safe_corridor,
        }
        if router_modifiers:
            metadata["temporal_router_modifiers"] = router_modifiers

        if allowed and temporal_snapshot.temporal_drift > thresholds.get("temporal_drift_threshold", 0.3):
            allowed = False
            reason = "temporal_drift_high"
        prediction_threshold = thresholds.get("temporal_prediction_error_threshold", 0.2)
        if allowed and temporal_snapshot.prediction_error > prediction_threshold:
            allowed = False
            reason = "temporal_prediction_error"

        predictive_collapse_threshold = thresholds.get("predictive_collapse_threshold", 0.8)
        predictive_accel_threshold = thresholds.get("predictive_acceleration_threshold", 0.4)
        foresight_warning = None

        if allowed and predictive_snapshot.collapse_risk >= predictive_collapse_threshold:
            allowed = False
            reason = "foresight_hold"
            metadata["foresight_reason"] = "predictive_collapse"
            metadata["foresight_warning"] = "predictive_collapse"

        if not allowed and reason == "foresight_hold" and "foresight_warning" not in metadata:
            metadata["foresight_warning"] = "predictive_collapse"
        else:
            history_ready = len(self._predictive_history) >= self._predictive_history_window
            if history_ready:
                accelerations = [
                    abs(entry.get("drift_acceleration", 0.0)) for entry in self._predictive_history
                ]
                if accelerations and all(acc >= predictive_accel_threshold for acc in accelerations):
                    foresight_warning = "predictive_acceleration"
                    metadata["foresight_warning"] = foresight_warning

        metadata["predictive_history_window"] = self._predictive_history_window

        result = GovernanceResult(
            allowed=allowed,
            reason=reason,
            ethics=ethics,
            snapshot=snapshot,
            metadata=metadata,
        )

        warning_label = metadata.get("foresight_warning")

        if record:
            self._last_result = result
            self._ledger.append(result.to_dict())
            record_governance_result(result)
            self._publish_to_mirror(result)
            if warning_label:
                record_predictive_warning(warning_label)
        return result

    def _publish_to_mirror(self, result: GovernanceResult) -> None:
        if not mirror_publish:
            return
        try:
            mirror_publish("governance.snapshot", result.snapshot, "governance", ttl=300.0)
            mirror_publish(
                "governance.ethics",
                [check.to_dict() for check in result.ethics],
                "governance",
                ttl=300.0,
            )
            mirror_publish(
                "governance.policy_scores",
                result.metadata,
                "governance",
                ttl=300.0,
            )
            mirror_publish("governance.final_decision", result.to_dict(), "governance", ttl=300.0)
            warning = result.metadata.get("foresight_warning")
            if warning:
                mirror_publish(
                    "governance.trajectory_warning",
                    {
                        "warning": warning,
                        "reason": result.metadata.get("foresight_reason"),
                        "collapse_risk": result.metadata.get("predictive_collapse_risk"),
                        "snapshot": result.snapshot.get("predictive"),
                    },
                    "governance",
                    ttl=180.0,
                )
        except Exception:
            return

    @property
    def last_result(self) -> Optional[GovernanceResult]:
        return self._last_result

    @property
    def ledger(self) -> GovernanceLedger:
        return self._ledger
