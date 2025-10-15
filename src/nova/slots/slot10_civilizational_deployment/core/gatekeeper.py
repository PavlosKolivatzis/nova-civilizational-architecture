"""Gatekeeper for Slot 10 deployment decisions using ACL registry gates."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List
import logging
import time
from .policy import Slot10Policy
from .health_feed import HealthFeedAdapter, MockHealthFeed

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
            health_snapshot={"slot8": slot8_health, "slot4": slot4_health}
        )

        # Store for metrics access
        self.last_gate_result = result
        return result
