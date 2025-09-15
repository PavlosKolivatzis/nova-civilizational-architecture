"""Observability metrics collection for Slot 8 Memory Lock & IDS system."""

import time
from collections import deque, defaultdict
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field


@dataclass
class MetricPoint:
    """Single metric data point with timestamp."""
    timestamp: float
    value: float
    labels: Dict[str, str] = field(default_factory=dict)


class Slot8MetricsCollector:
    """Metrics collector for Slot 8 observability.

    Emits metrics for TSDB consumption and dashboard visualization.
    """

    def __init__(self, retention_seconds: int = 3600):
        """Initialize metrics collector with retention period."""
        self.retention_seconds = retention_seconds
        self.metrics: Dict[str, deque] = defaultdict(lambda: deque(maxlen=1000))

        # Track recovery timing for MTTR distribution
        self.recovery_times: deque = deque(maxlen=100)
        self.quarantine_state_changes: deque = deque(maxlen=50)

    def record_integrity_score(self, score: float, context: Optional[Dict] = None) -> None:
        """Record integrity score metric."""
        self._record_metric("slot8.integrity_score", score, context or {})

    def record_quarantine_state(self, active: bool, time_in_state_s: float = 0.0) -> None:
        """Record quarantine state and duration."""
        self._record_metric("slot8.quarantine.active", 1.0 if active else 0.0)
        if time_in_state_s > 0:
            self._record_metric("slot8.quarantine.time_in_state_s", time_in_state_s)

        # Track state changes for analysis
        self.quarantine_state_changes.append({
            "timestamp": time.time(),
            "active": active,
            "duration": time_in_state_s
        })

    def record_recovery_mttr(self, mttr_seconds: float, context: Optional[Dict] = None) -> None:
        """Record Mean Time To Recovery metric."""
        self._record_metric("slot8.recovery.mttr_s", mttr_seconds, context or {})
        self.recovery_times.append({
            "timestamp": time.time(),
            "mttr": mttr_seconds,
            "context": context or {}
        })

    def record_repair_outcome(self, action: str, success: bool, duration_s: float) -> None:
        """Record repair action success rate and timing."""
        labels = {"action": action}
        self._record_metric("slot8.repair.success_rate", 1.0 if success else 0.0, labels)
        self._record_metric("slot8.repair.duration_s", duration_s, labels)

    def record_entropy_metrics(self, current: float, threshold: float,
                             baseline: float, is_anomalous: bool) -> None:
        """Record entropy monitoring metrics."""
        self._record_metric("slot8.entropy.score", current)
        self._record_metric("slot8.entropy.threshold", threshold)
        self._record_metric("slot8.entropy.baseline", baseline)
        self._record_metric("slot8.entropy.anomaly", 1.0 if is_anomalous else 0.0)

    def record_write_surge(self, count: int, threshold: int, window_s: int) -> None:
        """Record write surge detection event."""
        labels = {"window_s": str(window_s), "threshold": str(threshold)}
        self._record_metric("slot8.ids.write_surge.count", float(count), labels)

    def record_ids_event(self, event_type: str, threat_level: str, source_path: str) -> None:
        """Record IDS detection event."""
        labels = {"event_type": event_type, "threat_level": threat_level}
        self._record_metric("slot8.ids.events.total", 1.0, labels)

    def get_slo_compliance(self, window_seconds: int = 300) -> Dict[str, Any]:
        """Calculate SLO compliance metrics for dashboards."""
        current_time = time.time()
        cutoff_time = current_time - window_seconds

        # MTTR SLO compliance (≤ 5s)
        recent_recoveries = [r for r in self.recovery_times
                           if r["timestamp"] >= cutoff_time]
        mttr_violations = sum(1 for r in recent_recoveries if r["mttr"] > 5.0)
        mttr_slo = 1.0 - (mttr_violations / max(1, len(recent_recoveries)))

        # Quarantine flip SLO (≤ 1s activation)
        recent_activations = [q for q in self.quarantine_state_changes
                            if q["timestamp"] >= cutoff_time and q["active"]]
        flip_violations = sum(1 for q in recent_activations if q["duration"] > 1.0)
        flip_slo = 1.0 - (flip_violations / max(1, len(recent_activations)))

        # Current integrity status
        integrity_metrics = self.metrics.get("slot8.integrity_score", deque())
        current_integrity = integrity_metrics[-1].value if integrity_metrics else 0.0

        # Quarantine status
        quarantine_metrics = self.metrics.get("slot8.quarantine.active", deque())
        quarantine_active = bool(quarantine_metrics[-1].value) if quarantine_metrics else False

        return {
            "mttr_slo_compliance": mttr_slo,
            "quarantine_flip_slo_compliance": flip_slo,
            "current_integrity_score": current_integrity,
            "quarantine_active": quarantine_active,
            "recent_recoveries_count": len(recent_recoveries),
            "window_seconds": window_seconds,
            "deploy_gate_status": self._evaluate_deploy_gate()
        }

    def _evaluate_deploy_gate(self) -> Dict[str, Any]:
        """Evaluate Slot 10 deployment gate conditions."""
        integrity_metrics = self.metrics.get("slot8.integrity_score", deque())
        quarantine_metrics = self.metrics.get("slot8.quarantine.active", deque())

        # Current values
        integrity_score = integrity_metrics[-1].value if integrity_metrics else 0.0
        quarantine_active = bool(quarantine_metrics[-1].value) if quarantine_metrics else False

        # Recent recovery success rate (5 minute window)
        current_time = time.time()
        recent_recoveries = [r for r in self.recovery_times
                           if r["timestamp"] >= current_time - 300]

        if recent_recoveries:
            success_count = sum(1 for r in recent_recoveries if r["mttr"] <= 5.0)
            success_rate = success_count / len(recent_recoveries)
        else:
            success_rate = 1.0  # No recent failures, assume healthy

        # Gate conditions from ACL registry
        conditions = {
            "integrity_score_ok": integrity_score >= 0.7,
            "quarantine_inactive": not quarantine_active,
            "recovery_success_rate_ok": success_rate >= 0.8
        }

        gate_open = all(conditions.values())

        return {
            "gate_open": gate_open,
            "conditions": conditions,
            "values": {
                "integrity_score": integrity_score,
                "quarantine_active": quarantine_active,
                "recovery_success_rate_5m": success_rate
            }
        }

    def _record_metric(self, name: str, value: float, labels: Optional[Dict[str, str]] = None) -> None:
        """Internal method to record a metric point."""
        point = MetricPoint(
            timestamp=time.time(),
            value=value,
            labels=labels or {}
        )
        self.metrics[name].append(point)

        # Clean old metrics beyond retention
        cutoff_time = point.timestamp - self.retention_seconds
        while (self.metrics[name] and
               self.metrics[name][0].timestamp < cutoff_time):
            self.metrics[name].popleft()

    def export_prometheus_metrics(self) -> str:
        """Export metrics in Prometheus format for TSDB scraping."""
        lines = []
        current_time = time.time()

        for metric_name, points in self.metrics.items():
            if not points:
                continue

            # Get latest point
            latest = points[-1]

            # Convert metric name to Prometheus format
            prom_name = metric_name.replace(".", "_")

            # Add labels if present
            if latest.labels:
                label_str = ",".join(f'{k}="{v}"' for k, v in latest.labels.items())
                line = f"{prom_name}{{{label_str}}} {latest.value} {int(latest.timestamp * 1000)}"
            else:
                line = f"{prom_name} {latest.value} {int(latest.timestamp * 1000)}"

            lines.append(line)

        return "\n".join(lines)

    def get_dashboard_data(self, window_seconds: int = 3600) -> Dict[str, Any]:
        """Get formatted data for dashboard consumption."""
        current_time = time.time()
        cutoff_time = current_time - window_seconds

        dashboard_data = {}

        for metric_name, points in self.metrics.items():
            recent_points = [p for p in points if p.timestamp >= cutoff_time]
            if recent_points:
                dashboard_data[metric_name] = {
                    "current": recent_points[-1].value,
                    "min": min(p.value for p in recent_points),
                    "max": max(p.value for p in recent_points),
                    "avg": sum(p.value for p in recent_points) / len(recent_points),
                    "points": [{"ts": p.timestamp, "value": p.value} for p in recent_points[-100:]]
                }

        # Add SLO compliance data
        dashboard_data["slo_compliance"] = self.get_slo_compliance(window_seconds)

        return dashboard_data


# Global metrics collector instance
_metrics_collector: Optional[Slot8MetricsCollector] = None


def get_metrics_collector() -> Slot8MetricsCollector:
    """Get or create the global metrics collector."""
    global _metrics_collector
    if _metrics_collector is None:
        _metrics_collector = Slot8MetricsCollector()
    return _metrics_collector


def emit_metric(name: str, value: float, labels: Optional[Dict[str, str]] = None) -> None:
    """Convenience function to emit a metric."""
    get_metrics_collector()._record_metric(name, value, labels)