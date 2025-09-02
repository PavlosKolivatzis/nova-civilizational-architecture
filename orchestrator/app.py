from fastapi import FastAPI

from orchestrator.core.performance_monitor import PerformanceMonitor
from orchestrator.core.event_bus import EventBus, Event
from orchestrator.core.router import AdaptiveRouter
from orchestrator.core.circuit_breaker import CircuitBreaker

app = FastAPI()

# Monitor, bus and router are created once and reused across requests
monitor = PerformanceMonitor()
bus = EventBus(monitor=monitor)
cb = CircuitBreaker(monitor)
router = AdaptiveRouter(performance_monitor=monitor, circuit_breaker=cb)

# Optional: configure fallbacks
# router.fallback_map = {"slot6": "slot6_fallback"}

SLOT_REGISTRY = {}
try:  # pragma: no cover - illustrative orchestrator wiring
    from orchestrator.run import Orchestrator  # type: ignore

    orch = Orchestrator(per_call_timeout=2.0, max_retries=1)
except Exception:  # pragma: no cover - orchestrator runner not available
    orch = None


@app.get("/health")
async def health():
    return {
        "slots": {sid: monitor.get_slot_health(sid) for sid in SLOT_REGISTRY.keys()},
        "router_thresholds": {
            "latency_ms": router.latency_threshold_ms,
            "error_rate": router.error_threshold,
        },
        "circuit_breaker": router.cb.get_metrics() if getattr(router, "cb", None) else {},
    }


async def handle_request(target_slot: str, payload: dict, request_id: str):
    """Route request based on slot health and invoke the orchestrator."""
    slot, timeout = router.get_route(target_slot, original_timeout=2.0)
    evt = Event(target_slot=slot, payload=payload)
    await bus.publish("invoke", evt)
    slot_fn = SLOT_REGISTRY.get(slot)
    if orch and slot_fn:
        return await orch.invoke_slot(slot_fn, slot, payload, request_id, timeout=timeout)
    return None
