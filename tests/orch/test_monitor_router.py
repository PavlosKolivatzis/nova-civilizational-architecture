import asyncio
import pytest

from orchestrator.core.performance_monitor import PerformanceMonitor
from orchestrator.core.event_bus import EventBus, Event
from orchestrator.core.router import AdaptiveRouter


@pytest.mark.asyncio
async def test_monitor_records_and_router_fallback():
    mon = PerformanceMonitor()
    bus = EventBus(monitor=mon)
    router = AdaptiveRouter(mon, latency_threshold_ms=1.0, error_threshold=0.5)
    router.fallback_map = {"slot6": "slot6_fallback"}

    async def slow_handler(e: Event):
        await asyncio.sleep(0.01)
        return "ok"

    bus.subscribe("invoke", slow_handler)

    for _ in range(5):
        await bus.publish("invoke", Event(target_slot="slot6", payload={}))

    health = mon.get_slot_health("slot6")
    assert health["avg_latency_ms"] >= 1.0

    slot, _ = router.get_route("slot6")
    assert slot == "slot6_fallback"


@pytest.mark.asyncio
async def test_monitor_error_rate():
    mon = PerformanceMonitor()
    bus = EventBus(mon)

    async def failing(_):
        raise RuntimeError("boom")

    bus.subscribe("invoke", failing)

    with pytest.raises(RuntimeError):
        await bus.publish("invoke", Event(target_slot="slot9", payload={}))

    h = mon.get_slot_health("slot9")
    assert h["error_rate"] == 1.0
    assert h["throughput"] >= 1


@pytest.mark.asyncio
async def test_monitor_tracks_new_slots():
    mon = PerformanceMonitor()
    bus = EventBus(monitor=mon)

    async def handler(_):
        return "ok"

    bus.subscribe("invoke", handler)

    slots = [
        "slot02_deltathresh",
        "slot08_memory_ethics",
        "slot09_distortion_protection",
        "slot10_civilizational_deployment",
    ]

    for s in slots:
        await bus.publish("invoke", Event(target_slot=s, payload={}))

    for s in slots:
        h = mon.get_slot_health(s)
        assert h["throughput"] >= 1
