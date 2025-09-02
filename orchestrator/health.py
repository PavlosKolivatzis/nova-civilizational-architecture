"""Health monitoring and aggregation for the NOVA system."""

from typing import Any, Callable, Dict
import time


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


def health_payload(slot_registry, monitor, router, circuit_breaker=None) -> Dict[str, Any]:
    """Generate comprehensive health payload for the system."""
    cb_metrics = get_circuit_breaker_metrics(circuit_breaker)

    return {
        "slots": collect_slot_health(slot_registry, monitor),
        "router_thresholds": {
            "latency_ms": getattr(router, "latency_threshold_ms", None),
            "error_rate": getattr(router, "error_threshold", None),
            "timeout_multiplier": getattr(router, "multiplier", None),
            "timeout_cap_s": getattr(router, "timeout_cap", None),
        },
        "circuit_breaker": cb_metrics,
        "timestamp": time.time(),
    }


def collect_slot_selfchecks(slot_registry) -> dict:
    """Optional: Collect self-check health from each slot."""
    out = {}
    for sid, fn in slot_registry.items():
        mod = fn.__module__.split(".")
        package = ".".join(mod[:-1])  # naive; adjust per layout
        try:
            hc = __import__(package + ".health", fromlist=["health"])
            out[sid] = hc.health()
        except Exception:
            out[sid] = {"self_check": "n/a"}
    return out
