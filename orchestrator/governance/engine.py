from __future__ import annotations

import os
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
from orchestrator.predictive.pattern_detector import detect_patterns, PatternAlert
from orchestrator.predictive.consistency import compute_consistency_gap, ConsistencyProfile
from orchestrator.predictive.memory_resonance import get_memory_window
from orchestrator.predictive.ris_calculator import compute_ris, ris_to_dict

try:
    from src.nova.continuity.risk_reconciliation import get_unified_risk_field
except Exception:  # pragma: no cover
    def get_unified_risk_field() -> dict:  # type: ignore[misc]
        return {"alignment_score": 1.0, "composite_risk": 0.0, "risk_gap": 0.0}

try:
    from src.nova.continuity.meta_stability import (
        record_composite_risk_sample,
        get_meta_stability_snapshot,
        should_block_governance,
    )
except Exception:  # pragma: no cover
    def record_composite_risk_sample(composite_risk: float) -> None:  # type: ignore[misc]
        return
    def get_meta_stability_snapshot() -> dict:  # type: ignore[misc]
        return {"meta_instability": 0.0, "trend": "stable", "drift_velocity": 0.0, "sample_count": 0}
    def should_block_governance(meta_instability: float, threshold: float = 0.15) -> bool:  # type: ignore[misc]
        return False

try:  # pragma: no cover - metrics optional
    from orchestrator.prometheus_metrics import record_predictive_warning, record_consistency_gap, record_urf, record_mse
except Exception:  # pragma: no cover
    def record_predictive_warning(reason: str | None = None) -> None:  # type: ignore[misc]
        return
    def record_consistency_gap(gap_profile: dict) -> None:  # type: ignore[misc]
        return
    def record_urf(urf: dict) -> None:  # type: ignore[misc]
        return
    def record_mse(mse: dict) -> None:  # type: ignore[misc]
        return


def _urf_enabled() -> bool:
    """Check if URF integration is enabled via NOVA_ENABLE_URF flag."""
    return os.getenv("NOVA_ENABLE_URF", "0") == "1"


def _mse_enabled() -> bool:
    """Check if MSE integration is enabled via NOVA_ENABLE_MSE flag."""
    return os.getenv("NOVA_ENABLE_MSE", "0") == "1"


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
        self._governance_history: Deque[Dict[str, Any]] = deque(maxlen=50)  # EPD history
        self._router_history: Deque[Dict[str, Any]] = deque(maxlen=50)  # EPD history
        self._active_patterns: Dict[str, PatternAlert] = {}  # Debounce state
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

        # Step 5: Detect emergent patterns (EPD)
        if routing_decision:
            self._router_history.append({
                "timestamp": predictive_payload.get("timestamp", 0.0),
                "route": routing_decision.get("route", "unknown"),
                "penalty": routing_decision.get("penalty", 0.0),
                "stability_pressure": predictive_payload.get("stability_pressure", 0.0),
            })

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

        # Phase 9: Unified Risk Field (URF) governance gates (flag-gated)
        if _urf_enabled():
            urf = get_unified_risk_field()
            record_urf(urf)  # Record to Prometheus
            metadata["urf"] = {
                "alignment_score": urf.get("alignment_score", 1.0),
                "risk_gap": urf.get("risk_gap", 0.0),
                "composite_risk": urf.get("composite_risk", 0.0),
            }

            composite_risk_threshold = thresholds.get("urf_composite_risk_threshold", 0.7)
            alignment_score_threshold = thresholds.get("urf_alignment_threshold", 0.5)

            if allowed and urf.get("composite_risk", 0.0) >= composite_risk_threshold:
                allowed = False
                reason = "urf_composite_risk_high"
                metadata["urf_reason"] = f"composite_risk={urf.get('composite_risk', 0.0):.3f} >= {composite_risk_threshold}"

            if allowed and urf.get("alignment_score", 1.0) < alignment_score_threshold:
                allowed = False
                reason = "urf_alignment_low"
                metadata["urf_reason"] = f"alignment_score={urf.get('alignment_score', 1.0):.3f} < {alignment_score_threshold}"

            # Record composite_risk sample for MSE (if MSE enabled)
            if _mse_enabled():
                record_composite_risk_sample(urf.get("composite_risk", 0.0))

        # Phase 10: Meta-Stability Engine (MSE) governance gates (flag-gated)
        if _mse_enabled():
            mse = get_meta_stability_snapshot()
            record_mse(mse)  # Record to Prometheus
            metadata["mse"] = {
                "meta_instability": mse.get("meta_instability", 0.0),
                "trend": mse.get("trend", "stable"),
                "drift_velocity": mse.get("drift_velocity", 0.0),
            }

            mse_threshold = thresholds.get("mse_governance_threshold", 0.15)
            meta_instability = mse.get("meta_instability", 0.0)

            if allowed and should_block_governance(meta_instability, mse_threshold):
                allowed = False
                reason = "mse_meta_instability_high"
                metadata["mse_reason"] = f"meta_instability={meta_instability:.3f} >= {mse_threshold}, trend={mse.get('trend', 'unknown')}"

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

        # EPD pattern detection with debouncing (include current decision)
        pattern_alerts = self._detect_and_debounce_patterns(thresholds, {
            "timestamp": predictive_payload.get("timestamp", 0.0),
            "allowed": allowed,
            "reason": reason,
        })
        if pattern_alerts:
            metadata["pattern_alerts"] = [
                {
                    "type": alert.pattern_type,
                    "severity": alert.severity,
                    "window": (alert.window_start, alert.window_end),
                    "metadata": alert.metadata
                }
                for alert in pattern_alerts
            ]

        # MSC: Multi-slot consistency gap detection (Step 6)
        consistency_profile = self._compute_consistency_gap(
            state=state,
            slot07=slot07,
            predictive_snapshot=predictive_snapshot,
            pattern_alerts=pattern_alerts,
            thresholds=thresholds
        )
        if consistency_profile:
            metadata["consistency_gap"] = consistency_profile.to_dict()

            # Governance gating based on consistency
            gap_threshold = thresholds.get("consistency_gap_threshold", 0.6)
            severity_threshold = thresholds.get("consistency_severity_threshold", 0.7)

            if (consistency_profile.gap_score >= gap_threshold or
                consistency_profile.severity >= severity_threshold):
                if allowed:  # Only downgrade if not already blocked
                    allowed = False
                    reason = "consistency_gap"
                    metadata["consistency_reason"] = f"gap={consistency_profile.gap_score:.2f}, severity={consistency_profile.severity:.2f}"

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
            # Update governance history for EPD
            self._governance_history.append({
                "timestamp": predictive_payload.get("timestamp", 0.0),
                "allowed": allowed,
                "reason": reason,
            })
            self._ledger.append(result.to_dict())
            record_governance_result(result)
            self._publish_to_mirror(result)
            if warning_label:
                record_predictive_warning(warning_label)
            # Publish pattern alerts and increment metrics
            for alert in pattern_alerts:
                record_predictive_warning(reason=f"pattern_{alert.pattern_type}")
            # Record consistency gap metrics (Step 6)
            if consistency_profile:
                record_consistency_gap(consistency_profile.to_dict())

            # Sample TRSI for memory resonance (RC - Step 7)
            self._sample_memory_resonance(temporal_snapshot, predictive_payload.get("timestamp", 0.0))

            # Compute RIS for RC attestation (RC - Step 8)
            self._compute_and_publish_ris(temporal_snapshot, predictive_payload.get("timestamp", 0.0))

        return result

    def _detect_and_debounce_patterns(
        self,
        thresholds: Dict[str, Any],
        current_decision: Optional[Dict[str, Any]] = None
    ) -> list[PatternAlert]:
        """
        Detect patterns with debouncing logic (Gemini-3.0 requirement).

        Args:
            thresholds: Current threshold configuration
            current_decision: Current governance decision to include in history

        Returns list of new alerts (debounced). Manages active_patterns state.
        """
        import os

        if os.getenv("NOVA_ENABLE_EPD", "false").lower() != "true":
            return []

        # Get detection window from thresholds
        window_size = int(thresholds.get("epd_window_size", 20))
        cooldown_ticks = int(os.getenv("NOVA_PREDICTIVE_PATTERN_COOLDOWN", "20"))

        # Include current decision in history for detection
        gov_history = list(self._governance_history)
        if current_decision:
            gov_history.append(current_decision)

        # Run pattern detection
        detected = detect_patterns(
            predictive_history=list(self._predictive_history),
            governance_history=gov_history,
            router_history=list(self._router_history),
            window_size=window_size
        )

        # Filter out debounced patterns
        new_alerts = []
        for alert in detected:
            if alert.pattern_type not in self._active_patterns:
                # New pattern - add to active set
                self._active_patterns[alert.pattern_type] = {
                    "alert": alert,
                    "ticks": 0
                }
                new_alerts.append(alert)

        # Age out cooldowns
        expired = []
        for pattern_type, state in self._active_patterns.items():
            state["ticks"] += 1
            if state["ticks"] >= cooldown_ticks:
                expired.append(pattern_type)

        for pattern_type in expired:
            del self._active_patterns[pattern_type]

        return new_alerts

    def _compute_consistency_gap(
        self,
        state: Dict[str, Any],
        slot07: Dict[str, Any],
        predictive_snapshot: PredictiveSnapshot,
        pattern_alerts: list[PatternAlert],
        thresholds: Dict[str, Any]
    ) -> Optional[ConsistencyProfile]:
        """
        Compute multi-slot consistency gap (Step 6).

        Reads slot states from semantic mirror and computes cross-slot conflicts.
        """
        import os

        if os.getenv("NOVA_ENABLE_MSC", "false").lower() != "true":
            return None

        # Read slot states from semantic mirror (would use mirror.read in production)
        # For now, extract from state dict
        slot03_state = state.get("slot03", {})
        slot06_state = state.get("slot06", {})
        slot10_state = state.get("slot10", {})

        # Convert pattern alerts to dict format
        alert_dicts = [
            {
                "type": alert.pattern_type,
                "severity": alert.severity
            }
            for alert in pattern_alerts
        ]

        # Compute consistency profile
        profile = compute_consistency_gap(
            slot03_state=slot03_state,
            slot06_state=slot06_state,
            slot07_state=slot07,
            slot10_state=slot10_state,
            predictive_snapshot=predictive_snapshot.to_dict(),
            pattern_alerts=alert_dicts,
            timestamp=predictive_snapshot.timestamp
        )

        return profile

    def _sample_memory_resonance(self, temporal_snapshot: TemporalSnapshot, timestamp: float) -> None:
        """
        Sample TRSI for memory resonance tracking (Phase 7.0-RC).

        Extracts TRSI from temporal snapshot and adds to 7-day rolling window.
        Publishes memory stability to semantic mirror.

        Args:
            temporal_snapshot: Current temporal state
            timestamp: Event timestamp
        """
        import os

        if os.getenv("NOVA_ENABLE_MEMORY_RESONANCE", "false").lower() != "true":
            return

        # Get memory window singleton
        memory_window = get_memory_window()

        # Extract TRSI from temporal convergence score
        # (temporal_convergence_score is the canonical TRSI metric)
        trsi_value = temporal_snapshot.convergence_score

        # Add sample to rolling window
        memory_window.add_sample(
            trsi_value=trsi_value,
            timestamp=timestamp,
            source="temporal_engine"
        )

        # Publish to semantic mirror (every Nth sample to reduce overhead)
        sample_count = len(memory_window.trsi_history)
        if sample_count % 6 == 0:  # Every 6 hours
            memory_window.publish_to_mirror(ttl=3600.0)  # 1 hour TTL

    def _compute_and_publish_ris(self, temporal_snapshot: TemporalSnapshot, timestamp: float) -> None:
        """
        Compute Resonance Integrity Score (RIS) for RC attestation (Phase 7.0-RC).

        RIS = sqrt(M_s × E_c)
        Where:
            M_s = Memory Stability (7-day TRSI rolling window)
            E_c = Ethical Compliance (Slot06 principle_preservation or governance fallback)

        Publishes RIS to semantic mirror and Prometheus.

        Args:
            temporal_snapshot: Current temporal state
            timestamp: Event timestamp
        """
        import os

        if os.getenv("NOVA_ENABLE_MEMORY_RESONANCE", "false").lower() != "true":
            return  # RIS requires memory resonance enabled

        # Get memory window and compute stability
        memory_window = get_memory_window()
        memory_stability = memory_window.compute_memory_stability()

        # Compute RIS (ethical compliance resolved via hierarchy in ris_calculator)
        ris = compute_ris(memory_stability=memory_stability)

        # Store in governance state
        self._state["ris_score"] = ris

        # Publish to semantic mirror (key: predictive.ris_score)
        if mirror_publish:
            try:
                ris_snapshot = ris_to_dict(
                    ris=ris,
                    memory_stability=memory_stability,
                    ethical_compliance=1.0,  # Resolved internally by compute_ris
                    timestamp=timestamp
                )
                mirror_publish(
                    "predictive.ris_score",
                    ris_snapshot,
                    "governance",
                    ttl=3600.0  # 1 hour TTL
                )
            except Exception:  # pragma: no cover
                pass  # Fail silently (observability, not critical path)

        # Record to Prometheus
        try:
            from orchestrator.prometheus_metrics import record_ris_score
            record_ris_score(ris)
        except Exception:  # pragma: no cover
            pass  # Metrics optional

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
            # Publish pattern alerts (Step 5)
            pattern_alerts = result.metadata.get("pattern_alerts", [])
            if pattern_alerts:
                mirror_publish(
                    "predictive.pattern_alert",
                    pattern_alerts,
                    "governance",
                    ttl=180.0
                )
            # Publish consistency gap (Step 6)
            consistency_gap = result.metadata.get("consistency_gap")
            if consistency_gap:
                mirror_publish(
                    "predictive.consistency_gap",
                    consistency_gap,
                    "governance",
                    ttl=180.0
                )
        except Exception:
            return

    @property
    def last_result(self) -> Optional[GovernanceResult]:
        return self._last_result

    @property
    def ledger(self) -> GovernanceLedger:
        return self._ledger
