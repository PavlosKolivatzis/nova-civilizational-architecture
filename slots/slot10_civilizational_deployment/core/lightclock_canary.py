"""Light-Clock enhanced canary deployment controller."""
from __future__ import annotations
import os
import time
import logging
from dataclasses import dataclass
from typing import Optional, Dict, Any

from .canary import CanaryController, CanaryResult
from .lightclock_gatekeeper import LightClockGatekeeper, LightClockGateResult
from .policy import Slot10Policy
from .health_feed import HealthFeedAdapter, MockHealthFeed, RuntimeMetrics
from .audit import AuditLog
from .metrics import CanaryMetricsExporter

logger = logging.getLogger(__name__)


@dataclass
class LightClockCanaryResult(CanaryResult):
    """Extended canary result with Light-Clock context."""
    lightclock_gate_result: Optional[LightClockGateResult] = None
    coherence_adjustments: Optional[Dict[str, Any]] = None  # Fixed mutable default


class LightClockCanaryController(CanaryController):
    """Enhanced canary controller with Light-Clock phase coherence gating."""

    def __init__(
        self,
        policy: Slot10Policy,
        lightclock_gatekeeper: LightClockGatekeeper,
        health_feed: Optional[HealthFeedAdapter] = None,
        audit: Optional[AuditLog] = None,
        metrics_exporter: Optional[CanaryMetricsExporter] = None,
    ):
        # Initialize base controller with the Light-Clock gatekeeper
        super().__init__(policy, lightclock_gatekeeper, health_feed, audit, metrics_exporter)
        self.lightclock_gatekeeper = lightclock_gatekeeper

        # Light-Clock specific configuration
        self.coherence_thresholds = {
            "high_coherence_acceleration": 0.85,    # Allow faster promotion with high coherence
            "low_coherence_deceleration": 0.4,      # Slow down promotion with low coherence
            "minimal_coherence_block": 0.3          # Block promotion with minimal coherence
        }

        logger.info("Light-Clock enhanced canary controller initialized")

    def evaluate_stage(
        self,
        current_metrics: dict,
        slot08_metrics: dict,
        slot04_metrics: dict,
    ) -> LightClockCanaryResult:
        """Enhanced stage evaluation with Light-Clock coherence considerations."""
        if self.rollback_triggered:
            return LightClockCanaryResult(
                success=False,
                action="rollback",
                stage_idx=self.current_stage_idx,
                reason="Rollback already in progress",
                metrics={},
                lightclock_gate_result=None,
                coherence_adjustments={}
            )

        # Evaluate Light-Clock enhanced gate
        lightclock_gate_result = self.lightclock_gatekeeper.evaluate_deploy_gate(slot08_metrics, slot04_metrics)

        # Check if Light-Clock gate passes
        if not lightclock_gate_result.passed:
            return self._trigger_lightclock_rollback(
                f"Light-Clock gate failure: {lightclock_gate_result.failed_conditions}",
                lightclock_gate_result
            )

        current_stage = self.stages[self.current_stage_idx]

        # Invariant check: monotonic stage progression
        if self.current_stage_idx < 0 or self.current_stage_idx >= len(self.stages):
            return self._trigger_lightclock_rollback(
                f"Invalid stage index: {self.current_stage_idx}",
                lightclock_gate_result
            )

        # Apply coherence-based timing adjustments
        coherence_adjustments = self._apply_coherence_adjustments(lightclock_gate_result)

        # Adjusted promotion velocity guard
        adjusted_min_gap = coherence_adjustments.get("adjusted_min_promotion_gap", self.policy.min_promotion_gap_s)
        if adjusted_min_gap > 0 and self._last_promotion_ts is not None:
            gap = time.time() - self._last_promotion_ts
            if gap < adjusted_min_gap:
                return LightClockCanaryResult(
                    success=True,
                    action="continue",
                    stage_idx=self.current_stage_idx,
                    reason=f"Coherence-adjusted promotion gap: {gap:.1f}s < {adjusted_min_gap:.1f}s",
                    metrics={"time_since_last_promotion": gap, "adjusted_min_gap": adjusted_min_gap},
                    lightclock_gate_result=lightclock_gate_result,
                    coherence_adjustments=coherence_adjustments
                )

        # Adjusted minimum stage duration
        adjusted_min_duration = coherence_adjustments.get("adjusted_min_stage_duration", self.policy.min_stage_duration_s)
        if current_stage.duration < adjusted_min_duration:
            return LightClockCanaryResult(
                success=True,
                action="continue",
                stage_idx=self.current_stage_idx,
                reason=f"Coherence-adjusted stage duration {current_stage.duration:.1f}s < {adjusted_min_duration:.1f}s",
                metrics={"stage_duration": current_stage.duration, "adjusted_min_duration": adjusted_min_duration},
                lightclock_gate_result=lightclock_gate_result,
                coherence_adjustments=coherence_adjustments
            )

        # SLO checks vs. baseline (with coherence-adjusted thresholds)
        slo_violation = self._check_coherence_adjusted_slo_violations(current_metrics, coherence_adjustments)
        if slo_violation:
            current_stage.slo_violations += 1
            return self._trigger_lightclock_rollback(
                f"Coherence-adjusted SLO violation: {slo_violation}",
                lightclock_gate_result
            )

        # Stage timeout protection
        if current_stage.duration > self.policy.canary_stage_timeout_s:
            return self._trigger_lightclock_rollback(
                f"Stage timeout: {current_stage.duration:.1f}s > {self.policy.canary_stage_timeout_s}s",
                lightclock_gate_result
            )

        # All good → promote or complete
        return self._promote_lightclock_stage(lightclock_gate_result, coherence_adjustments)

    def _apply_coherence_adjustments(self, gate_result: LightClockGateResult) -> Dict[str, Any]:
        """Apply timing and threshold adjustments based on phase_lock coherence."""
        adjustments = {
            "coherence_level": gate_result.coherence_level,
            "phase_lock_value": gate_result.phase_lock_value,
            "adjustment_reason": ""
        }

        # Skip adjustments if Light-Clock is disabled or no phase_lock available
        if os.getenv("NOVA_LIGHTCLOCK_GATING", "1") == "0" or gate_result.phase_lock_value is None:
            adjustments["adjustment_reason"] = "lightclock_disabled_or_unavailable"
            return adjustments

        phase_lock = gate_result.phase_lock_value
        coherence_level = gate_result.coherence_level

        # High coherence: allow faster promotion
        if phase_lock > self.coherence_thresholds["high_coherence_acceleration"]:
            adjustments["adjusted_min_promotion_gap"] = max(0, self.policy.min_promotion_gap_s * 0.7)
            adjustments["adjusted_min_stage_duration"] = max(30, self.policy.min_stage_duration_s * 0.8)
            adjustments["error_rate_multiplier"] = self.policy.error_rate_multiplier * 1.1  # Slightly more permissive
            adjustments["adjustment_reason"] = "high_coherence_acceleration"
            logger.debug(f"Applied high coherence acceleration for phase_lock={phase_lock:.3f}")

        # Low coherence: slower promotion, tighter thresholds
        elif phase_lock < self.coherence_thresholds["low_coherence_deceleration"]:
            adjustments["adjusted_min_promotion_gap"] = self.policy.min_promotion_gap_s * 1.5
            adjustments["adjusted_min_stage_duration"] = self.policy.min_stage_duration_s * 1.2
            adjustments["error_rate_multiplier"] = self.policy.error_rate_multiplier * 0.9  # More strict
            adjustments["latency_p95_multiplier"] = self.policy.latency_p95_multiplier * 0.95  # More strict
            adjustments["adjustment_reason"] = "low_coherence_deceleration"
            logger.debug(f"Applied low coherence deceleration for phase_lock={phase_lock:.3f}")

        # Minimal coherence: significant deceleration
        elif phase_lock < self.coherence_thresholds["minimal_coherence_block"]:
            adjustments["adjusted_min_promotion_gap"] = self.policy.min_promotion_gap_s * 2.0
            adjustments["adjusted_min_stage_duration"] = self.policy.min_stage_duration_s * 1.5
            adjustments["error_rate_multiplier"] = self.policy.error_rate_multiplier * 0.8  # Much more strict
            adjustments["latency_p95_multiplier"] = self.policy.latency_p95_multiplier * 0.9  # Much more strict
            adjustments["adjustment_reason"] = "minimal_coherence_extreme_caution"
            logger.debug(f"Applied minimal coherence extreme caution for phase_lock={phase_lock:.3f}")

        # Medium coherence: standard behavior
        else:
            adjustments["adjustment_reason"] = "medium_coherence_standard"

        return adjustments

    def _check_coherence_adjusted_slo_violations(self, current_metrics: dict, coherence_adjustments: Dict[str, Any]) -> Optional[str]:
        """Check SLO violations with coherence-adjusted thresholds."""
        baseline = self.frozen_baseline or self.baseline_metrics
        if not baseline:
            return None

        # Use coherence-adjusted multipliers if available
        error_rate_multiplier = coherence_adjustments.get("error_rate_multiplier", self.policy.error_rate_multiplier)
        latency_p95_multiplier = coherence_adjustments.get("latency_p95_multiplier", self.policy.latency_p95_multiplier)

        # Error rate check
        baseline_errors = float(baseline.get("error_rate", 0.0))
        current_errors = float(current_metrics.get("error_rate", 0.0))
        if current_errors > baseline_errors * error_rate_multiplier:
            return (
                f"error_rate {current_errors:.3f} > "
                f"coherence_adjusted_baseline {baseline_errors:.3f} * {error_rate_multiplier:.2f}"
            )

        # Latency p95 check
        baseline_p95 = float(baseline.get("latency_p95", 0.0))
        current_p95 = float(current_metrics.get("latency_p95", 0.0))
        if current_p95 > baseline_p95 * latency_p95_multiplier:
            return (
                f"latency_p95 {current_p95:.3f} > "
                f"coherence_adjusted_baseline {baseline_p95:.3f} * {latency_p95_multiplier:.2f}"
            )

        # Saturation check (no coherence adjustment)
        current_saturation = float(current_metrics.get("saturation", 0.0))
        if current_saturation > self.policy.saturation_threshold:
            return f"saturation {current_saturation:.3f} > {self.policy.saturation_threshold}"

        return None

    def _promote_lightclock_stage(self, gate_result: LightClockGateResult, coherence_adjustments: Dict[str, Any]) -> LightClockCanaryResult:
        """Promote to next stage with Light-Clock context."""
        # Use base promotion logic
        base_result = self._promote_stage()

        # Create enhanced result
        lightclock_result = LightClockCanaryResult(
            success=base_result.success,
            action=base_result.action,
            stage_idx=base_result.stage_idx,
            reason=base_result.reason,
            metrics=base_result.metrics,
            lightclock_gate_result=gate_result,
            coherence_adjustments=coherence_adjustments
        )

        # Add coherence context to metrics
        lightclock_result.metrics.update({
            "phase_lock_value": gate_result.phase_lock_value,
            "coherence_level": gate_result.coherence_level,
            "coherence_adjustment": coherence_adjustments.get("adjustment_reason", "none")
        })

        return lightclock_result

    def _trigger_lightclock_rollback(self, reason: str, gate_result: LightClockGateResult) -> LightClockCanaryResult:
        """Trigger rollback with Light-Clock context."""
        # Use base rollback logic
        base_result = self._trigger_rollback(reason)

        # Create enhanced result
        lightclock_result = LightClockCanaryResult(
            success=base_result.success,
            action=base_result.action,
            stage_idx=base_result.stage_idx,
            reason=base_result.reason,
            metrics=base_result.metrics,
            lightclock_gate_result=gate_result,
            coherence_adjustments={}
        )

        # Add Light-Clock context to rollback metrics
        lightclock_result.metrics.update({
            "phase_lock_value": gate_result.phase_lock_value,
            "tri_score": gate_result.tri_score,
            "slot9_policy": gate_result.slot9_policy,
            "coherence_level": gate_result.coherence_level,
            "lightclock_failures": gate_result.failed_conditions
        })

        return lightclock_result

    def tick(self) -> LightClockCanaryResult:
        """Light-Clock enhanced tick with coherence-aware evaluation."""
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
            # NEW: forward TRI to gatekeeper if health feed has it
            "tri_score": getattr(s4, "tri_score", None),
        }
        current = {
            "error_rate": rt.error_rate,
            "latency_p95": rt.latency_p95,
            "saturation": rt.saturation,
        }

        result = self.evaluate_stage(current, slot08, slot04)

        # Export enhanced metrics if configured
        self._emit_lightclock_metrics(result, current, slot08, slot04)

        return result

    def _emit_lightclock_metrics(self, result: LightClockCanaryResult, runtime_metrics: dict, slot08_metrics: dict, slot04_metrics: dict):
        """Emit enhanced metrics with Light-Clock context."""
        if not self.metrics_exporter or not self.metrics_exporter.should_export():
            return

        # Capture base canary state
        metrics = self.metrics_exporter.capture_canary_state(self)

        # Add Light-Clock specific metrics
        if result.lightclock_gate_result:
            metrics.update({
                "lightclock_phase_lock": result.lightclock_gate_result.phase_lock_value,
                "lightclock_tri_score": result.lightclock_gate_result.tri_score,
                "lightclock_slot9_policy": result.lightclock_gate_result.slot9_policy,
                "lightclock_coherence_level": result.lightclock_gate_result.coherence_level,
                "lightclock_gate_passes": result.lightclock_gate_result.lightclock_passes,
                "lightclock_gate_reason": result.lightclock_gate_result.lightclock_reason
            })

        if result.coherence_adjustments:
            metrics.update({
                "coherence_adjustment_type": result.coherence_adjustments.get("adjustment_reason"),
                "adjusted_min_promotion_gap": result.coherence_adjustments.get("adjusted_min_promotion_gap"),
                "adjusted_min_stage_duration": result.coherence_adjustments.get("adjusted_min_stage_duration")
            })

        # Update with gate result and export
        updated_metrics = self.metrics_exporter.update_metrics(
            metrics,
            gate_result=result.lightclock_gate_result,
            runtime_metrics=runtime_metrics,
            rollback_reason=result.reason if result.action == "rollback" else ""
        )

        self.metrics_exporter.export_metrics(updated_metrics)