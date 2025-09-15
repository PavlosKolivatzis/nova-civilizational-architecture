"""Gatekeeper for Slot 10 deployment decisions using ACL registry gates."""
from __future__ import annotations
from dataclasses import dataclass
from typing import Optional, Dict, Any, List
import logging
from .policy import Slot10Policy

logger = logging.getLogger(__name__)

@dataclass
class GateResult:
    passed: bool
    failed_conditions: List[str]

class Gatekeeper:
    """Evaluates deploy gates from Slot 8/4 health signals."""

    def __init__(self, policy: Optional[Slot10Policy] = None):
        self.policy = policy or Slot10Policy()

    def evaluate_deploy_gate(self, slot08: Dict[str, Any], slot04: Dict[str, Any]) -> GateResult:
        fails: List[str] = []

        # Slot 8 conditions
        if slot08.get("quarantine_active", False):
            fails.append("slot08_quarantine")
        if slot08.get("integrity_score", 0.0) < self.policy.slot08_integrity_threshold:
            fails.append("slot08_integrity")
        rr = slot08.get("recent_recoveries", {}).get("success_rate_5m", 0.0)
        if rr < self.policy.slot08_recovery_rate_threshold:
            fails.append("slot08_recovery_rate")

        # Slot 4 conditions
        if slot04.get("safe_mode_active", False):
            fails.append("slot04_safe_mode")
        if slot04.get("drift_z", 0.0) >= self.policy.slot04_drift_z_threshold:
            fails.append("slot04_drift")

        passed = not fails
        if not passed:
            logger.warning("Gate HOLD: %s", fails)
        return GateResult(passed=passed, failed_conditions=fails)