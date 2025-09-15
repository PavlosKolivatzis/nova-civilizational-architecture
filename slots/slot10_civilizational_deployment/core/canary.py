"""Progressive canary deployment with autonomous rollback."""
from __future__ import annotations
from dataclasses import dataclass
from typing import Optional, Dict, Any
import time
import logging
from .policy import Slot10Policy
from .gatekeeper import Gatekeeper

logger = logging.getLogger(__name__)

@dataclass
class CanaryStage:
    percentage: float
    start_time: Optional[float] = None
    end_time: Optional[float] = None
    slo_violations: int = 0

    @property
    def duration(self) -> float:
        if self.start_time and self.end_time:
            return self.end_time - self.start_time
        if self.start_time:
            return time.time() - self.start_time
        return 0.0

@dataclass
class CanaryResult:
    success: bool
    action: str  # "start" | "continue" | "promote" | "rollback"
    stage_idx: int
    reason: str
    metrics: Dict[str, Any]

class CanaryController:
    """Progressive delivery controlled by ACL gates."""

    def __init__(self, policy: Slot10Policy, gatekeeper: Gatekeeper):
        self.policy = policy
        self.gatekeeper = gatekeeper
        self.current_stage_idx = 0
        self.stages = [CanaryStage(pct) for pct in policy.canary_stages]
        self.baseline_metrics: Dict[str, float] = {}
        self.rollback_triggered = False

    def start_deployment(self, baseline_metrics: Dict[str, float]) -> CanaryResult:
        self.baseline_metrics = baseline_metrics
        self.current_stage_idx = 0
        self.rollback_triggered = False
        self.stages[0].start_time = time.time()
        logger.info("Starting canary at %.1f%%", self.stages[0].percentage * 100.0)
        return CanaryResult(True, "start", 0, f"Initialized at {self.stages[0].percentage:.1%}",
                            {"stage_count": len(self.stages)})

    def evaluate_stage(self, current_metrics: Dict[str, float], slot08_metrics: Dict[str, Any], slot04_metrics: Dict[str, Any]) -> CanaryResult:
        if self.rollback_triggered:
            return CanaryResult(False, "rollback", self.current_stage_idx, "Rollback already in progress", {})

        # Gates first
        gate = self.gatekeeper.evaluate_deploy_gate(slot08_metrics, slot04_metrics)
        if not gate.passed:
            return self._trigger_rollback(f"Gate failure: {gate.failed_conditions}")

        stage = self.stages[self.current_stage_idx]

        # Min duration
        if stage.duration < self.policy.min_stage_duration_s:
            return CanaryResult(True, "continue", self.current_stage_idx,
                                f"Stage duration {stage.duration:.2f}s < {self.policy.min_stage_duration_s}s",
                                {"stage_duration": stage.duration})

        # SLOs
        viol = self._check_slo_violations(current_metrics)
        if viol:
            stage.slo_violations += 1
            return self._trigger_rollback(f"SLO violation: {viol}")

        # Timeout
        if stage.duration > self.policy.canary_stage_timeout_s:
            return self._trigger_rollback(f"Stage timeout: {stage.duration:.2f}s > {self.policy.canary_stage_timeout_s}s")

        # Healthy → promote or finish
        return self._promote_stage()

    def _check_slo_violations(self, current: Dict[str, float]) -> Optional[str]:
        if not self.baseline_metrics:
            return None
        # error rate
        base_err = self.baseline_metrics.get("error_rate", 0.0)
        cur_err = current.get("error_rate", 0.0)
        if cur_err > base_err * self.policy.error_rate_multiplier:
            return f"error_rate {cur_err:.4f} > baseline {base_err:.4f} * {self.policy.error_rate_multiplier}"
        # latency p95
        base_p95 = self.baseline_metrics.get("latency_p95", 0.0)
        cur_p95 = current.get("latency_p95", 0.0)
        if cur_p95 > base_p95 * self.policy.latency_p95_multiplier:
            return f"latency_p95 {cur_p95:.2f} > baseline {base_p95:.2f} * {self.policy.latency_p95_multiplier}"
        # saturation
        cur_sat = current.get("saturation", 0.0)
        if cur_sat > self.policy.saturation_threshold:
            return f"saturation {cur_sat:.3f} > {self.policy.saturation_threshold}"
        return None

    def _promote_stage(self) -> CanaryResult:
        stage = self.stages[self.current_stage_idx]
        stage.end_time = time.time()
        if self.current_stage_idx >= len(self.stages) - 1:
            # completed
            total = sum(s.duration for s in self.stages)
            logger.info("Canary completed")
            return CanaryResult(True, "promote", self.current_stage_idx, "Deployment completed",
                                {"total_duration": total})
        # advance
        self.current_stage_idx += 1
        nxt = self.stages[self.current_stage_idx]
        nxt.start_time = time.time()
        logger.info("Promote to stage %d (%.1f%%)", self.current_stage_idx, nxt.percentage * 100.0)
        return CanaryResult(True, "promote", self.current_stage_idx,
                            f"Promoted to {nxt.percentage:.1%}",
                            {"previous_stage_duration": stage.duration})

    def _trigger_rollback(self, reason: str) -> CanaryResult:
        self.rollback_triggered = True
        stage = self.stages[self.current_stage_idx]
        stage.end_time = time.time()
        logger.warning("Triggering rollback: %s", reason)
        return CanaryResult(False, "rollback", self.current_stage_idx, reason,
                            {"stage_duration": stage.duration, "slo_violations": stage.slo_violations})

    @property
    def current_percentage(self) -> float:
        return self.stages[self.current_stage_idx].percentage if self.current_stage_idx < len(self.stages) else 1.0