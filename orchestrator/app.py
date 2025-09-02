from orchestrator.core.performance_monitor import PerformanceMonitor
from orchestrator.core.event_bus import EventBus, Event
from orchestrator.core.router import AdaptiveRouter

# Monitor, bus and router are created once and reused across requests
monitor = PerformanceMonitor()
bus = EventBus(monitor=monitor)
router = AdaptiveRouter(performance_monitor=monitor)

# Optional: configure fallbacks
# router.fallback_map = {"slot6": "slot6_fallback"}

try:  # pragma: no cover - illustrative orchestrator wiring
    from orchestrator.run import Orchestrator  # type: ignore
    orch = Orchestrator(per_call_timeout=2.0, max_retries=1)
except Exception:  # pragma: no cover - orchestrator runner not available
    orch = None
    SLOT_REGISTRY = {}


async def handle_request(target_slot: str, payload: dict, request_id: str):
    """Route request based on slot health and invoke the orchestrator."""
    routed_slot = router.get_route(target_slot)
    evt = Event(target_slot=routed_slot, payload=payload)
    await bus.publish("invoke", evt)
    slot_fn = SLOT_REGISTRY.get(routed_slot) if 'SLOT_REGISTRY' in globals() else None
    if orch and slot_fn:
        return await orch.invoke_slot(slot_fn, routed_slot, payload, request_id)
    return None
