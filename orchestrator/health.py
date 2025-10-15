# ruff: noqa: E402
"""Health monitoring and aggregation for the NOVA system."""

import importlib
from typing import Any, Callable, Dict, Optional
import time

from src_bootstrap import ensure_src_on_path


def _prometheus_header(metric: str, mtype: str, help_text: str) -> str:
    """Format a Prometheus metric header."""
    return f"# HELP {metric} {help_text}\n# TYPE {metric} {mtype}"


def collect_slot_health(slot_registry: Dict[str, Callable], monitor) -> Dict[str, Any]:
    """Aggregate per-slot health from the PerformanceMonitor."""
    return {slot_id: monitor.get_slot_health(slot_id) for slot_id in slot_registry.keys()}


def get_circuit_breaker_metrics(circuit_breaker):
    """Extract metrics from circuit breaker if available."""
    if not circuit_breaker:
        return {}
    try:
        return circuit_breaker.get_metrics()
    except AttributeError:
        metrics: Dict[str, Any] = {}
        for attr in ["state", "failure_count", "success_count", "last_failure"]:
            if hasattr(circuit_breaker, attr):
                metrics[attr] = getattr(circuit_breaker, attr)
        return metrics


def collect_slot_selfchecks(slot_registry: Dict[str, Callable]) -> Dict[str, Any]:
    """Collect self-check health from each slot's health module."""
    self_checks: Dict[str, Any] = {}

    ensure_src_on_path()
    for slot_id in slot_registry.keys():
        module = None
        import_error_reason: Optional[str] = None
        for module_path in (f"nova.slots.{slot_id}.health",):
            try:
                module = importlib.import_module(module_path)
                break
            except ImportError:
                continue
            except Exception as exc:  # pragma: no cover - defensive
                import_error_reason = str(exc)
                module = None
                break
        if module is None:
            if import_error_reason:
                self_checks[slot_id] = {"self_check": "error", "reason": import_error_reason}
            else:
                self_checks[slot_id] = {
                    "self_check": "n/a",
                    "reason": "health module not found",
                }
            continue

        try:
            self_checks[slot_id] = module.health()
        except Exception as exc:  # pragma: no cover - defensive
            self_checks[slot_id] = {
                "self_check": "error",
                "reason": str(exc),
            }

    return self_checks








def health_payload(slot_registry, monitor, router, circuit_breaker=None) -> Dict[str, Any]:
    """Generate comprehensive health payload for the system."""
    cb_metrics = get_circuit_breaker_metrics(circuit_breaker)
    
    # Include Flow Fabric metrics if enabled
    flow_health = {}
    try:
        from .flow_metrics import flow_metrics
        from .config import config
        if config.FLOW_METRICS_ENABLED:
            flow_health = flow_metrics.get_flow_health_summary()
    except ImportError:
        pass  # Flow metrics not available

    payload = {
        "slots": collect_slot_health(slot_registry, monitor),
        "slot_self_checks": collect_slot_selfchecks(slot_registry),
        "router_thresholds": {
            "latency_ms": getattr(router, "latency_threshold_ms", None),
            "error_rate": getattr(router, "error_threshold", None),
            "timeout_multiplier": getattr(router, "multiplier", None),
            "timeout_cap_s": getattr(router, "timeout_cap", None),
        },
        "circuit_breaker": cb_metrics,
        "timestamp": time.time(),
        "version": "1.0.0",
    }
    
    # Add flow fabric health if available
    if flow_health:
        payload["flow_fabric"] = flow_health
    
    return payload


def prometheus_metrics(slot_registry: Dict[str, Callable], monitor) -> str:
    """Generate Prometheus-compatible metrics for all slots."""
    lines = []

    # Average latency metric
    metric = "slot_avg_latency_ms"
    lines.append(_prometheus_header(metric, "gauge", "Average latency in milliseconds per slot"))
    for slot_id in slot_registry.keys():
        health = monitor.get_slot_health(slot_id)
        lines.append(f'{metric}{{slot="{slot_id}"}} {health.get("avg_latency_ms", 0.0)}')

    # Error rate metric
    metric = "slot_error_rate"
    lines.append(_prometheus_header(metric, "gauge", "Error rate per slot"))
    for slot_id in slot_registry.keys():
        health = monitor.get_slot_health(slot_id)
        lines.append(f'{metric}{{slot="{slot_id}"}} {health.get("error_rate", 0.0)}')

    # Throughput metric
    metric = "slot_throughput"
    lines.append(_prometheus_header(metric, "gauge", "Throughput per slot"))
    for slot_id in slot_registry.keys():
        health = monitor.get_slot_health(slot_id)
        lines.append(f'{metric}{{slot="{slot_id}"}} {health.get("throughput", 0)}')

    return "\n".join(lines) + "\n"
