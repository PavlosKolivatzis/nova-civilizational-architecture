"""Gatekeeper for Slot 10 deployment decisions using ACL registry gates."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List
import logging
import time
from .policy import Slot10Policy
from .health_feed import HealthFeedAdapter, MockHealthFeed

try:
    from src.nova.continuity.risk_reconciliation import get_unified_risk_field
except Exception:
    def get_unified_risk_field() -> dict:  # type: ignore[misc]
        return {"alignment_score": 1.0, "composite_risk": 0.0, "risk_gap": 0.0}

try:
    from src.nova.continuity.meta_stability import (
        record_composite_risk_sample,
        get_meta_stability_snapshot,
        should_block_deployment,
    )
except Exception:
    def record_composite_risk_sample(composite_risk: float) -> None:  # type: ignore[misc]
        return
    def get_meta_stability_snapshot() -> dict:  # type: ignore[misc]
        return {"meta_instability": 0.0, "trend": "stable", "drift_velocity": 0.0, "sample_count": 0}
    def should_block_deployment(meta_instability: float, threshold: float = 0.12) -> bool:  # type: ignore[misc]
        return False

try:
    from src.nova.continuity.operational_regime import get_operational_regime
except Exception:
    def get_operational_regime() -> dict:  # type: ignore[misc]
        return {}

try:  # pragma: no cover - metrics optional
    from orchestrator.prometheus_metrics import record_orp
except Exception:  # pragma: no cover
    def record_orp(snapshot: dict, transition_from: str | None = None) -> None:  # type: ignore[misc]
        return

def _urf_enabled() -> bool:
    """Check if URF integration is enabled via NOVA_ENABLE_URF flag."""
    import os
    return os.getenv("NOVA_ENABLE_URF", "0") == "1"

def _mse_enabled() -> bool:
    """Check if MSE integration is enabled via NOVA_ENABLE_MSE flag."""
    import os
    return os.getenv("NOVA_ENABLE_MSE", "0") == "1"


def _orp_enabled() -> bool:
    """Check if ORP integration is enabled via NOVA_ENABLE_ORP flag."""
    import os
    return os.getenv("NOVA_ENABLE_ORP", "0") == "1"


logger = logging.getLogger(__name__)

@dataclass
class GateResult:
    passed: bool
    failed_conditions: List[str]
    evaluation_time_s: float = 0.0
    health_snapshot: Dict[str, Any] = field(default_factory=dict)

class Gatekeeper:
    """Evaluates deploy gates from live Slot 8/4 health signals."""

    def __init__(self, policy: Optional[Slot10Policy] = None, health_feed: Optional[HealthFeedAdapter] = None):
        self.policy = policy or Slot10Policy()
        self.health_feed = health_feed or MockHealthFeed()
        self.last_gate_result: Optional[GateResult] = None

    def evaluate_deploy_gate(self, slot08: Optional[Dict[str, Any]] = None, slot04: Optional[Dict[str, Any]] = None) -> GateResult:
        """Evaluate deployment gate using live health feeds or provided dicts (for testing)."""
        start_time = time.time()
        fails: List[str] = []

        # Use provided dicts for testing, otherwise pull from health feed
        if slot08 is not None and slot04 is not None:
            # Legacy dict-based interface for tests
            slot8_health = slot08
            slot4_health = slot04
        else:
            # Live health feed interface
            slot8_data = self.health_feed.get_slot8_health()
            slot4_data = self.health_feed.get_slot4_health()

            slot8_health = {
                "quarantine_active": slot8_data.quarantine_active,
                "integrity_score": slot8_data.integrity_score,
                "recent_recoveries": slot8_data.recent_recoveries,
                "checksum_mismatch": slot8_data.checksum_mismatch,
                "tamper_evidence": slot8_data.tamper_evidence
            }
            slot4_health = {
                "safe_mode_active": slot4_data.safe_mode_active,
                "drift_z": slot4_data.drift_z
            }

        # Slot 8 conditions
        if slot8_health.get("quarantine_active", False):
            fails.append("slot08_quarantine")
        if slot8_health.get("integrity_score", 0.0) < self.policy.slot08_integrity_threshold:
            fails.append("slot08_integrity")
        rr = slot8_health.get("recent_recoveries", {}).get("success_rate_5m", 0.0)
        if rr < self.policy.slot08_recovery_rate_threshold:
            fails.append("slot08_recovery_rate")

        # Slot 4 conditions
        if slot4_health.get("safe_mode_active", False):
            fails.append("slot04_safe_mode")
        if slot4_health.get("drift_z", 0.0) >= self.policy.slot04_drift_z_threshold:
            fails.append("slot04_drift")

        # Data guard conditions (for slot4_data_guard gate)
        if slot8_health.get("checksum_mismatch", False):
            fails.append("slot08_checksum_mismatch")
        if slot8_health.get("tamper_evidence", False):
            fails.append("slot08_tamper_evidence")

        # Phase 9: URF deployment gates (flag-gated)
        composite_risk = 0.0
        alignment_score = 1.0
        risk_gap = 0.0
        if _urf_enabled():
            urf = get_unified_risk_field()
            composite_risk = urf.get("composite_risk", 0.0)
            alignment_score = urf.get("alignment_score", 1.0)
            risk_gap = urf.get("risk_gap", 0.0)

            # Block deployment if composite risk too high
            if composite_risk >= self.policy.urf_composite_risk_threshold:
                fails.append("urf_composite_risk_high")

            # Block deployment if risk signals divergent
            if alignment_score < self.policy.urf_alignment_threshold:
                fails.append("urf_alignment_low")

            # Block deployment if risk gap too wide
            if risk_gap > self.policy.urf_risk_gap_threshold:
                fails.append("urf_risk_gap_high")

            # Record composite_risk sample for MSE (if MSE enabled)
            if _mse_enabled():
                record_composite_risk_sample(composite_risk)

        # Phase 10: MSE deployment gates (flag-gated)
        meta_instability = 0.0
        mse_trend = "stable"
        if _mse_enabled():
            mse = get_meta_stability_snapshot()
            meta_instability = mse.get("meta_instability", 0.0)
            mse_trend = mse.get("trend", "stable")

            # Block deployment if meta-instability too high
            if should_block_deployment(meta_instability, self.policy.mse_deployment_threshold):
                fails.append("mse_meta_instability_high")

        # Phase 11: ORP deployment posture (flag-gated)
        orp_snapshot: Dict[str, Any] = {}
        if _orp_enabled():
            try:
                orp_snapshot = get_operational_regime()
                record_orp(orp_snapshot)
                posture = orp_snapshot.get("posture_adjustments", {}) or {}
                regime = str(orp_snapshot.get("regime", "normal")).lower()
                if posture.get("deployment_freeze"):
                    fails.append("orp_deployment_freeze")
                if regime in {"emergency_stabilization", "recovery"}:
                    logger.warning("ORP recommends rollback: regime=%s", regime)
            except Exception:
                logger.debug("ORP evaluation failed; continuing without ORP deployment gates", exc_info=True)

        passed = not fails
        evaluation_time = time.time() - start_time

        if not passed:
            logger.warning("Gate HOLD: %s (eval_time=%.3fs)", fails, evaluation_time)
        else:
            logger.debug("Gate PASS (eval_time=%.3fs)", evaluation_time)

        result = GateResult(
            passed=passed,
            failed_conditions=fails,
            evaluation_time_s=evaluation_time,
            health_snapshot={
                "slot8": slot8_health,
                "slot4": slot4_health,
                "urf": {
                    "composite_risk": composite_risk,
                    "alignment_score": alignment_score,
                    "risk_gap": risk_gap,
                },
                "mse": {
                    "meta_instability": meta_instability,
                    "trend": mse_trend,
                },
                "orp": orp_snapshot or {"regime": "normal"},
            }
        )

        # Store for metrics access
        self.last_gate_result = result
        return result
