"""Health monitoring and aggregation for the NOVA system."""

import importlib
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


def collect_slot_selfchecks(slot_registry: Dict[str, Callable]) -> Dict[str, Any]:
    """Collect self-check health from each slot's health module."""
    self_checks: Dict[str, Any] = {}

    for slot_id in slot_registry.keys():
        try:
            module_path = f"slots.{slot_id}.health"
            health_module = importlib.import_module(module_path)
            self_checks[slot_id] = health_module.health()
        except ImportError:
            self_checks[slot_id] = {
                "self_check": "n/a",
                "reason": "health module not found",
            }
        except Exception as e:  # pragma: no cover - defensive
            self_checks[slot_id] = {"self_check": "error", "reason": str(e)}

    return self_checks


def health_payload(slot_registry, monitor, router, circuit_breaker=None) -> Dict[str, Any]:
    """Generate comprehensive health payload for the system."""
    cb_metrics = get_circuit_breaker_metrics(circuit_breaker)

    return {
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
