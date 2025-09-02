"""
Health monitoring and aggregation for the NOVA system.
"""
from typing import Dict, Any, Callable


def collect_slot_health(slot_registry: Dict[str, Callable], monitor) -> Dict[str, Any]:
    """Aggregate per-slot health from the PerformanceMonitor."""
    return {slot_id: monitor.get_slot_health(slot_id) for slot_id in slot_registry.keys()}


def health_payload(slot_registry, monitor, router, circuit_breaker=None) -> Dict[str, Any]:
    """Generate comprehensive health payload for the system."""
    return {
        "slots": collect_slot_health(slot_registry, monitor),
        "router_thresholds": {
            "latency_ms": getattr(router, "latency_threshold_ms", None),
            "error_rate": getattr(router, "error_threshold", None),
        },
        "circuit_breaker": (circuit_breaker.get_metrics() if circuit_breaker else {}),
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
