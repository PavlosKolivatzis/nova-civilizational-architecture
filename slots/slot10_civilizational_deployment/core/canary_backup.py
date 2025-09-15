# slots/slot10_civilizational_deployment/core/canary.py
"""Progressive canary deployment with autonomous rollback."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Dict, Any
import time
import logging

from .policy import Slot10Policy
from .gatekeeper import Gatekeeper
from .health_feed import HealthFeedAdapter, MockHealthFeed

logger = logging.getLogger(__name__)


@dataclass
class CanaryStage:
    """Represents a single canary deployment stage."""
    percentage: float
    start_time: Optional[float] = None
    end_time: Optional[float] = None
    slo_violations: int = 0

    @property
    def duration(self) -> float:
        if self.start_time and self.end_time:
            return self.end_time - self.start_time
        elif self.start_time:
            return time.time() - self.start_time
        return 0.0


@dataclass
class CanaryResult:
    """Result of canary operation."""
    success: bool
    action: str  # "start", "promote", "rollback", "continue", "block"
    stage_idx: int
    reason: str
    metrics: dict[str, Any]


class CanaryController:
    """Progressive delivery controlled by ACL gates."""

    def __init__(
        self,
        policy: Slot10Policy,
        gatekeeper: Gatekeeper,
        health_feed: Optional[HealthFeedAdapter] = None,
    ):
        self.policy = policy
        self.gatekeeper = gatekeeper
        self.health_feed = health_feed or MockHealthFeed()
        self.current_stage_idx = 0
        self.stages = [CanaryStage(pct) for pct in policy.canary_stages]
        self.baseline_metrics: Dict[str, float] = {}
        self.rollback_triggered = False

    def start_deployment(self, baseline_metrics: dict) -> CanaryResult:
        """Initialize canary deployment with baseline metrics."""
        self.baseline_metrics = baseline_metrics
        self.current_stage_idx = 0
        self.rollback_triggered = False

        # Start first stage
        self.stages[0].start_time = time.time()
        logger.info("Starting canary deployment at %.1f%%", self.stages[0].percentage * 100)

        return CanaryResult(
            success=True,
            action="start",
            stage_idx=0,
            reason=f"Initialized at {self.stages[0].percentage:.1%}",
            metrics={"stage_count": len(self.stages)},
        )

    def tick(self, feed: Optional[HealthFeedAdapter] = None) -> CanaryResult:
        """
        Convenience method: pull live health + runtime metrics and evaluate current stage.
        Keeps testability by allowing an override feed.
        """
        hf = feed or self.health_feed or MockHealthFeed()

        s8 = hf.get_slot8_health()
        s4 = hf.get_slot4_health()
        rt = hf.get_runtime_metrics()

        current = {"error_rate": rt.error_rate, "latency_p95": rt.latency_p95, "saturation": rt.saturation}
        slot08 = {
            "integrity_score": s8.integrity_score,
            "quarantine_active": s8.quarantine_active,
            "recent_recoveries": s8.recent_recoveries,
            "checksum_mismatch": s8.checksum_mismatch,
            "tamper_evidence": s8.tamper_evidence,
        }
        slot04 = {"safe_mode_active": s4.safe_mode_active, "drift_z": s4.drift_z}

        return self.evaluate_stage(current, slot08, slot04)

    def evaluate_stage(
        self,
        current_metrics: dict,
        slot08_metrics: dict,
        slot04_metrics: dict,
    ) -> CanaryResult:
        """
        Evaluate current canary stage and decide next action.

        Backwards-compatible signature for existing tests, but you can now call
        `tick()` to auto-pull metrics via HealthFeed.
        """
        if self.rollback_triggered:
            return CanaryResult(
                success=False,
                action="rollback",
                stage_idx=self.current_stage_idx,
                reason="Rollback already in progress",
                metrics={},
            )

        # Gate conditions first (uses dicts we pass here; Gatekeeper still supports live feed when args omitted)
        gate_result = self.gatekeeper.evaluate_deploy_gate(slot08_metrics, slot04_metrics)
        if not gate_result.passed:
            return self._trigger_rollback(f"Gate failure: {gate_result.failed_conditions}")

        current_stage = self.stages[self.current_stage_idx]

        # Minimum stage duration
        if current_stage.duration < self.policy.min_stage_duration_s:
            return CanaryResult(
                success=True,
                action="continue",
                stage_idx=self.current_stage_idx,
                reason=f"Stage duration {current_stage.duration:.1f}s < {self.policy.min_stage_duration_s}s",
                metrics={"stage_duration": current_stage.duration},
            )

        # SLO checks vs baseline
        slo_violation = self._check_slo_violations(current_metrics)
        if slo_violation:
            current_stage.slo_violations += 1
            return self._trigger_rollback(f"SLO violation: {slo_violation}")

        # Stage timeout
        if current_stage.duration > self.policy.canary_stage_timeout_s:
            return self._trigger_rollback(
                f"Stage timeout: {current_stage.duration:.1f}s > {self.policy.canary_stage_timeout_s}s"
            )

        # Healthy → promote/complete
        return self._promote_stage()

    def _check_slo_violations(self, current_metrics: dict) -> Optional[str]:
        """Check if current metrics violate SLOs compared to baseline."""
        if not self.baseline_metrics:
            return None

        # Error rate
        baseline_errors = float(self.baseline_metrics.get("error_rate", 0.0))
        current_errors = float(current_metrics.get("error_rate", 0.0))
        if current_errors > baseline_errors * self.policy.error_rate_multiplier:
            return (
                f"error_rate {current_errors:.4f} > baseline {baseline_errors:.4f} * "
                f"{self.policy.error_rate_multiplier}"
            )

        # Latency p95
        baseline_p95 = float(self.baseline_metrics.get("latency_p95", 0.0))
        current_p95 = float(current_metrics.get("latency_p95", 0.0))
        if current_p95 > baseline_p95 * self.policy.latency_p95_multiplier:
            return (
                f"latency_p95 {current_p95:.3f} > baseline {baseline_p95:.3f} * "
                f"{self.policy.latency_p95_multiplier}"
            )

        # Saturation
        current_saturation = float(current_metrics.get("saturation", 0.0))
        if current_saturation > self.policy.saturation_threshold:
            return f"saturation {current_saturation:.3f} > {self.policy.saturation_threshold}"

        return None

    def _promote_stage(self) -> CanaryResult:
        """Promote to next stage or complete deployment."""
        current_stage = self.stages[self.current_stage_idx]
        current_stage.end_time = time.time()

        if self.current_stage_idx >= len(self.stages) - 1:
            # Deployment complete
            logger.info("Canary deployment completed successfully")
            return CanaryResult(
                success=True,
                action="promote",
                stage_idx=self.current_stage_idx,
                reason="Deployment completed",
                metrics={"total_duration": sum(s.duration for s in self.stages)},
            )

        # Move to next stage
        self.current_stage_idx += 1
        next_stage = self.stages[self.current_stage_idx]
        next_stage.start_time = time.time()

        logger.info("Promoting to stage %d: %.1f%%", self.current_stage_idx, next_stage.percentage * 100)

        return CanaryResult(
            success=True,
            action="promote",
            stage_idx=self.current_stage_idx,
            reason=f"Promoted to {next_stage.percentage:.1%}",
            metrics={"previous_stage_duration": current_stage.duration},
        )

    def _trigger_rollback(self, reason: str) -> CanaryResult:
        """Trigger autonomous rollback."""
        self.rollback_triggered = True
        current_stage = self.stages[self.current_stage_idx]
        current_stage.end_time = time.time()

        logger.warning("Triggering rollback: %s", reason)

        return CanaryResult(
            success=False,
            action="rollback",
            stage_idx=self.current_stage_idx,
            reason=reason,
            metrics={"stage_duration": current_stage.duration, "slo_violations": current_stage.slo_violations},
        )

    @property
    def current_percentage(self) -> float:
        """Get current deployment percentage."""
        if self.current_stage_idx < len(self.stages):
            return self.stages[self.current_stage_idx].percentage
        return 1.0