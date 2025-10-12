"""Canary deployment metrics export for observability."""

from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, Any, Optional, List
import time
import logging

logger = logging.getLogger(__name__)


@dataclass
class CanaryMetrics:
    """Current canary deployment metrics snapshot."""
    # Deployment state
    deployment_active: bool = False
    stage_idx: int = 0
    stage_percentage: float = 0.0
    total_stages: int = 0

    # Timing metrics
    deployment_start_ts: Optional[float] = None
    stage_start_ts: Optional[float] = None
    stage_duration_s: float = 0.0
    total_duration_s: float = 0.0

    # Gate and SLO status
    gate_status: str = "unknown"  # "pass" | "fail" | "unknown"
    gate_failed_conditions: List[str] = None
    slo_violation_count: int = 0

    # Performance metrics
    error_rate: float = 0.0
    latency_p95: float = 0.0
    saturation: float = 0.0

    # Rollback metrics
    rollback_triggered: bool = False
    rollback_reason: str = ""

    def __post_init__(self):
        if self.gate_failed_conditions is None:
            self.gate_failed_conditions = []


class CanaryMetricsExporter:
    """Export canary deployment metrics for monitoring systems."""

    def __init__(self, export_interval_s: float = 30.0):
        self.export_interval_s = export_interval_s
        self.last_export_ts = 0.0
        self.metrics_history: List[CanaryMetrics] = []
        self.max_history = 100  # Keep last 100 snapshots

    def should_export(self) -> bool:
        """Check if it's time to export metrics."""
        return time.time() - self.last_export_ts >= self.export_interval_s

    def capture_canary_state(self, controller) -> CanaryMetrics:
        """Capture current state from CanaryController."""
        now = time.time()

        # Get current stage info
        current_stage = None
        if controller.current_stage_idx < len(controller.stages):
            current_stage = controller.stages[controller.current_stage_idx]

        # Calculate durations
        stage_duration = current_stage.duration if current_stage else 0.0
        deployment_start = controller.stages[0].start_time if controller.stages else now
        total_duration = now - deployment_start if deployment_start else 0.0

        metrics = CanaryMetrics(
            deployment_active=not controller.rollback_triggered,
            stage_idx=controller.current_stage_idx,
            stage_percentage=controller.current_percentage,
            total_stages=len(controller.stages),
            deployment_start_ts=deployment_start,
            stage_start_ts=current_stage.start_time if current_stage else None,
            stage_duration_s=stage_duration,
            total_duration_s=total_duration,
            slo_violation_count=current_stage.slo_violations if current_stage else 0,
            rollback_triggered=controller.rollback_triggered,
        )

        return metrics

    def update_metrics(self, metrics: CanaryMetrics, gate_result=None, runtime_metrics=None, rollback_reason: str = "") -> CanaryMetrics:
        """Update metrics with gate and runtime data."""
        if gate_result:
            metrics.gate_status = "pass" if gate_result.passed else "fail"
            metrics.gate_failed_conditions = gate_result.failed_conditions or []

        if runtime_metrics:
            metrics.error_rate = runtime_metrics.get("error_rate", 0.0)
            metrics.latency_p95 = runtime_metrics.get("latency_p95", 0.0)
            metrics.saturation = runtime_metrics.get("saturation", 0.0)

        if rollback_reason:
            metrics.rollback_reason = rollback_reason

        return metrics

    def export_metrics(self, metrics: CanaryMetrics) -> Dict[str, Any]:
        """Export metrics in a format suitable for monitoring systems."""
        now = time.time()
        self.last_export_ts = now

        # Add to history
        self.metrics_history.append(metrics)
        if len(self.metrics_history) > self.max_history:
            self.metrics_history.pop(0)

        # Create exportable metrics dict
        exported = {
            "timestamp": now,
            "deploy_stage_pct": metrics.stage_percentage,
            "deploy_stage_idx": metrics.stage_idx,
            "deploy_total_stages": metrics.total_stages,
            "deploy_active": 1 if metrics.deployment_active else 0,
            "deploy_duration_s": metrics.total_duration_s,
            "stage_duration_s": metrics.stage_duration_s,

            # Gate metrics
            "gate_status": 1 if metrics.gate_status == "pass" else 0,
            "gate_failed_conditions_count": len(metrics.gate_failed_conditions),

            # SLO metrics
            "slo_violations": metrics.slo_violation_count,
            "error_rate": metrics.error_rate,
            "latency_p95_ms": metrics.latency_p95,
            "saturation_pct": metrics.saturation * 100,

            # Rollback metrics
            "rollback_triggered": 1 if metrics.rollback_triggered else 0,
        }

        # Add failed condition labels if any
        if metrics.gate_failed_conditions:
            for i, condition in enumerate(metrics.gate_failed_conditions[:5]):  # Limit to 5
                exported[f"gate_fail_condition_{i}"] = condition

        logger.debug("Exported canary metrics: %s", exported)
        return exported

    def get_prometheus_metrics(self, metrics: CanaryMetrics) -> str:
        """Export metrics in Prometheus format."""
        exported = self.export_metrics(metrics)

        prometheus_lines = []

        # Add help and type annotations
        prometheus_lines.extend([
            "# HELP slot10_deploy_stage_pct Current canary deployment stage percentage",
            "# TYPE slot10_deploy_stage_pct gauge",
            f"slot10_deploy_stage_pct {exported['deploy_stage_pct']:.3f}",
            "",
            "# HELP slot10_deploy_active Whether canary deployment is active (1) or not (0)",
            "# TYPE slot10_deploy_active gauge",
            f"slot10_deploy_active {exported['deploy_active']}",
            "",
            "# HELP slot10_gate_status Gate evaluation status (1=pass, 0=fail)",
            "# TYPE slot10_gate_status gauge",
            f"slot10_gate_status {exported['gate_status']}",
            "",
            "# HELP slot10_slo_violations Current stage SLO violation count",
            "# TYPE slot10_slo_violations counter",
            f"slot10_slo_violations {exported['slo_violations']}",
            "",
            "# HELP slot10_error_rate Current error rate",
            "# TYPE slot10_error_rate gauge",
            f"slot10_error_rate {exported['error_rate']:.6f}",
            "",
            "# HELP slot10_latency_p95_ms 95th percentile latency in milliseconds",
            "# TYPE slot10_latency_p95_ms gauge",
            f"slot10_latency_p95_ms {exported['latency_p95_ms']:.3f}",
            "",
            "# HELP slot10_rollback_triggered Whether rollback was triggered (1) or not (0)",
            "# TYPE slot10_rollback_triggered gauge",
            f"slot10_rollback_triggered {exported['rollback_triggered']}",
        ])

        return "\n".join(prometheus_lines)

    def get_recent_history(self, count: int = 10) -> List[CanaryMetrics]:
        """Get recent metrics history."""
        return self.metrics_history[-count:] if self.metrics_history else []

    def reset_history(self):
        """Clear metrics history."""
        self.metrics_history.clear()
        self.last_export_ts = 0.0