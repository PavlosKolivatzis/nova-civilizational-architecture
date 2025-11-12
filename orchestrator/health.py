# ruff: noqa: E402
"""Health monitoring and aggregation for the NOVA system."""

import importlib
import threading
import time
from typing import Any, Callable, Dict, Optional

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


# Cache for slot health modules to avoid repeated imports
_slot_health_module_cache: Dict[str, Any] = {}
_selfcheck_cache: Dict[str, tuple[float, Dict[str, Any]]] = {}
_SELF_CHECK_TTL = 1.0  # seconds
_timestamp_lock = threading.Lock()
_last_timestamp = 0.0


def clear_slot_health_cache():
    """Clear the slot health module cache. Useful for testing."""
    global _slot_health_module_cache
    _slot_health_module_cache.clear()
    _selfcheck_cache.clear()


def collect_slot_selfchecks(slot_registry: Dict[str, Callable]) -> Dict[str, Any]:
    """Collect self-check health from each slot's health module.

    Uses module caching to avoid repeated imports and reduce overhead.
    """
    self_checks: Dict[str, Any] = {}

    ensure_src_on_path()
    for slot_id in slot_registry.keys():
        cached_result = _selfcheck_cache.get(slot_id)
        now = time.time()
        if cached_result and now - cached_result[0] < _SELF_CHECK_TTL:
            self_checks[slot_id] = cached_result[1]
            continue

        # Check cache first
        if slot_id in _slot_health_module_cache:
            module = _slot_health_module_cache[slot_id]
            if module is None:  # Cached failure
                self_checks[slot_id] = {
                    "self_check": "n/a",
                    "reason": "health module not found (cached)",
                }
                continue
        else:
            # Import and cache the module
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

            # Cache the result (even if None)
            _slot_health_module_cache[slot_id] = module

            if module is None:
                if import_error_reason:
                    self_checks[slot_id] = {"self_check": "error", "reason": import_error_reason}
                else:
                    self_checks[slot_id] = {
                        "self_check": "n/a",
                        "reason": "health module not found",
                    }
                continue

        # Call the health() function
        try:
            self_checks[slot_id] = module.health()
        except Exception as exc:  # pragma: no cover - defensive
            self_checks[slot_id] = {
                "self_check": "error",
                "reason": str(exc),
            }
        else:
            _selfcheck_cache[slot_id] = (now, self_checks[slot_id])

    return self_checks

def _unique_timestamp() -> float:
    """Return a monotonically increasing timestamp (seconds)."""
    global _last_timestamp
    now = time.time()
    with _timestamp_lock:
        if now <= _last_timestamp:
            now = _last_timestamp + 0.001  # 1ms step ensures uniqueness within float precision
        _last_timestamp = now
    return now
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
        "timestamp": _unique_timestamp(),
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
