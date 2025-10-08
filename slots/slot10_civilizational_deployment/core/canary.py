"""Progressive canary deployment with autonomous rollback."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Dict, Any
import time
import logging

from .policy import Slot10Policy
from .gatekeeper import Gatekeeper
from .health_feed import HealthFeedAdapter, MockHealthFeed, RuntimeMetrics
from .audit import AuditLog
from .metrics import CanaryMetricsExporter

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
    action: str          # "start", "continue", "promote", "rollback", "block"
    stage_idx: int
    reason: str
    metrics: Dict[str, Any]


class CanaryController:
    """Progressive delivery controlled by ACL gates."""

    def __init__(
        self,
        policy: Slot10Policy,
        gatekeeper: Gatekeeper,
        health_feed: Optional[HealthFeedAdapter] = None,
        audit: Optional[AuditLog] = None,
        metrics_exporter: Optional[CanaryMetricsExporter] = None,
    ):
        self.policy = policy
        self.gatekeeper = gatekeeper
        self.health_feed = health_feed or MockHealthFeed()
        self.audit = audit
        self.metrics_exporter = metrics_exporter

        self.current_stage_idx = 0
        self.stages = [CanaryStage(pct) for pct in policy.canary_stages]
        self.baseline_metrics: Dict[str, float] = {}
        self.frozen_baseline: Optional[Dict[str, float]] = None
        self.rollback_triggered = False
        self._last_promotion_ts: Optional[float] = None

    def start_deployment(self, baseline_metrics: dict) -> CanaryResult:
        """Initialize canary deployment with frozen baseline metrics."""
        self.baseline_metrics = baseline_metrics or {}
        # Freeze baseline to prevent drift during deployment
        self.frozen_baseline = dict(self.baseline_metrics)
        self.current_stage_idx = 0
        self.rollback_triggered = False
        self._last_promotion_ts = None

        # Start first stage
        self.stages[0].start_time = time.time()

        logger.info("Starting canary deployment at %.1f%%", self.stages[0].percentage * 100.0)
        logger.info("Frozen baseline: %s", self.frozen_baseline)

        # Audit logging
        if self.audit:
            self.audit.record(
                action="start",
                stage_idx=0,
                reason=f"Initialized at {self.stages[0].percentage:.1%}",
                pct_from=0.0,
                pct_to=self.stages[0].percentage,
                metrics={"stage_count": len(self.stages), "frozen_baseline": self.frozen_baseline}
            )

        return CanaryResult(
            success=True,
            action="start",
            stage_idx=0,
            reason=f"Initialized at {self.stages[0].percentage:.1%}",
            metrics={"stage_count": len(self.stages), "frozen_baseline": self.frozen_baseline},
        )

    # Internal evaluator if the caller passes metrics explicitly
    def evaluate_stage(
        self,
        current_metrics: dict,
        slot08_metrics: dict,
        slot04_metrics: dict,
    ) -> CanaryResult:
        if self.rollback_triggered:
            return CanaryResult(
                success=False,
                action="rollback",
                stage_idx=self.current_stage_idx,
                reason="Rollback already in progress",
                metrics={},
            )

        # Check deploy gate first
        gate_result = self.gatekeeper.evaluate_deploy_gate(slot08_metrics, slot04_metrics)
        if not gate_result.passed:
            return self._trigger_rollback(f"Gate failure: {gate_result.failed_conditions}")

        current_stage = self.stages[self.current_stage_idx]

        # Invariant check: monotonic stage progression (no jumps backward)
        if self.current_stage_idx < 0 or self.current_stage_idx >= len(self.stages):
            return self._trigger_rollback(f"Invalid stage index: {self.current_stage_idx}")

        # Promotion velocity guard (disabled when min_promotion_gap_s == 0)
        if self.policy.min_promotion_gap_s > 0 and self._last_promotion_ts is not None:
            gap = time.time() - self._last_promotion_ts
            if gap < self.policy.min_promotion_gap_s:
                return CanaryResult(
                    success=True,
                    action="continue",
                    stage_idx=self.current_stage_idx,
                    reason=f"Promotion velocity limit: {gap:.1f}s < {self.policy.min_promotion_gap_s}s",
                    metrics={"time_since_last_promotion": gap}
                )

        # Minimum stage dwell time
        if current_stage.duration < self.policy.min_stage_duration_s:
            return CanaryResult(
                success=True,
                action="continue",
                stage_idx=self.current_stage_idx,
                reason=f"Stage duration {current_stage.duration:.1f}s < {self.policy.min_stage_duration_s}s",
                metrics={"stage_duration": current_stage.duration},
            )

        # SLO checks vs. baseline
        slo_violation = self._check_slo_violations(current_metrics)
        if slo_violation:
            current_stage.slo_violations += 1
            return self._trigger_rollback(f"SLO violation: {slo_violation}")

        # Stage timeout protection
        if current_stage.duration > self.policy.canary_stage_timeout_s:
            return self._trigger_rollback(
                f"Stage timeout: {current_stage.duration:.1f}s > {self.policy.canary_stage_timeout_s}s"
            )

        # All good → promote or complete
        return self._promote_stage()

    def _check_slo_violations(self, current_metrics: dict) -> Optional[str]:
        """Check if current metrics violate SLOs compared to frozen baseline."""
        # Use frozen baseline to prevent drift during deployment
        baseline = self.frozen_baseline or self.baseline_metrics
        if not baseline:
            return None

        # Error rate
        baseline_errors = float(baseline.get("error_rate", 0.0))
        current_errors = float(current_metrics.get("error_rate", 0.0))
        if current_errors > baseline_errors * self.policy.error_rate_multiplier:
            return (
                f"error_rate {current_errors:.3f} > "
                f"frozen_baseline {baseline_errors:.3f} * {self.policy.error_rate_multiplier}"
            )

        # Latency p95
        baseline_p95 = float(baseline.get("latency_p95", 0.0))
        current_p95 = float(current_metrics.get("latency_p95", 0.0))
        if current_p95 > baseline_p95 * self.policy.latency_p95_multiplier:
            return (
                f"latency_p95 {current_p95:.3f} > "
                f"frozen_baseline {baseline_p95:.3f} * {self.policy.latency_p95_multiplier}"
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

        # Last stage -> completed rollout
        if self.current_stage_idx >= len(self.stages) - 1:
            total = sum(s.duration for s in self.stages)
            self._last_promotion_ts = time.time()
            logger.info("Canary deployment completed successfully (total %.2fs)", total)
            return CanaryResult(
                success=True,
                action="promote",
                stage_idx=self.current_stage_idx,
                reason="Deployment completed",
                metrics={"total_duration": total},
            )

        # Next stage
        self.current_stage_idx += 1
        next_stage = self.stages[self.current_stage_idx]
        next_stage.start_time = time.time()
        self._last_promotion_ts = next_stage.start_time  # Track promotion timing

        logger.info("Promoting to stage %d: %.1f%%", self.current_stage_idx, next_stage.percentage * 100.0)

        # Audit logging
        if self.audit:
            self.audit.record(
                action="promote",
                stage_idx=self.current_stage_idx,
                reason=f"Promoted to {next_stage.percentage:.1%}",
                pct_from=current_stage.percentage,
                pct_to=next_stage.percentage,
                metrics={
                    "previous_stage_duration": current_stage.duration,
                    "promotion_timestamp": self._last_promotion_ts
                }
            )

        return CanaryResult(
            success=True,
            action="promote",
            stage_idx=self.current_stage_idx,
            reason=f"Promoted to {next_stage.percentage:.1%}",
            metrics={
                "previous_stage_duration": current_stage.duration,
                "promotion_timestamp": self._last_promotion_ts
            },
        )

    def _trigger_rollback(self, reason: str) -> CanaryResult:
        """Trigger autonomous rollback."""
        self.rollback_triggered = True
        stage = self.stages[self.current_stage_idx]
        stage.end_time = time.time()
        logger.warning("Triggering rollback: %s", reason)

        # Audit logging
        if self.audit:
            self.audit.record(
                action="rollback",
                stage_idx=self.current_stage_idx,
                reason=reason,
                pct_from=stage.percentage,
                pct_to=0.0,
                metrics={
                    "stage_duration": stage.duration,
                    "slo_violations": stage.slo_violations,
                }
            )

        return CanaryResult(
            success=False,
            action="rollback",
            stage_idx=self.current_stage_idx,
            reason=reason,
            metrics={
                "stage_duration": stage.duration,
                "slo_violations": stage.slo_violations,
            },
        )

    def tick(self) -> CanaryResult:
        """Pull live health + metrics, evaluate current stage, and act."""
        # Gather live signals
        s8 = self.health_feed.get_slot8_health()
        s4 = self.health_feed.get_slot4_health()
        rt: RuntimeMetrics = self.health_feed.get_runtime_metrics()

        # Make plain dicts for evaluator
        slot08 = {
            "integrity_score": s8.integrity_score,
            "quarantine_active": s8.quarantine_active,
            "recent_recoveries": s8.recent_recoveries,
            "checksum_mismatch": getattr(s8, "checksum_mismatch", False),
            "tamper_evidence": getattr(s8, "tamper_evidence", False),
        }
        slot04 = {
            "safe_mode_active": s4.safe_mode_active,
            "drift_z": s4.drift_z,
        }
        current = {
            "error_rate": rt.error_rate,
            "latency_p95": rt.latency_p95,
            "saturation": rt.saturation,
        }

        result = self.evaluate_stage(current, slot08, slot04)

        # Export metrics if configured
        self._emit_metrics(result, current, slot08, slot04)

        return result

    @property
    def current_percentage(self) -> float:
        """Get current stage percentage for metrics."""
        if self.current_stage_idx < len(self.stages):
            return self.stages[self.current_stage_idx].percentage
        return 1.0

    def _emit_metrics(self, result: CanaryResult, runtime_metrics: dict, slot08_metrics: dict, slot04_metrics: dict):
        """Emit metrics to exporter if configured."""
        if not self.metrics_exporter or not self.metrics_exporter.should_export():
            return

        # Capture current canary state
        metrics = self.metrics_exporter.capture_canary_state(self)

        # Update with gate result if available
        gate_result = self.gatekeeper.last_gate_result if hasattr(self.gatekeeper, 'last_gate_result') else None

        # Update metrics with runtime and gate data
        updated_metrics = self.metrics_exporter.update_metrics(
            metrics,
            gate_result=gate_result,
            runtime_metrics=runtime_metrics,
            rollback_reason=result.reason if result.action == "rollback" else ""
        )

        # Export metrics
        self.metrics_exporter.export_metrics(updated_metrics)