from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

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

    def __init__(self, ledger: Optional[GovernanceLedger] = None):
        self._ledger = ledger or GovernanceLedger()
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

        snapshot = {
            "tri_signal": tri_signal,
            "slot07": slot07,
            "slot10": slot10,
            "thresholds": thresholds,
        }

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
        }

        result = GovernanceResult(
            allowed=allowed,
            reason=reason,
            ethics=ethics,
            snapshot=snapshot,
            metadata=metadata,
        )

        if record:
            self._last_result = result
            self._ledger.append(result.to_dict())
            record_governance_result(result)
            self._publish_to_mirror(result)
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
        except Exception:
            return

    @property
    def last_result(self) -> Optional[GovernanceResult]:
        return self._last_result

    @property
    def ledger(self) -> GovernanceLedger:
        return self._ledger
