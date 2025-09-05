import time
import tracemalloc
import pytest

from orchestrator.core.event_bus import EventBus, Event


@pytest.mark.asyncio
async def test_enhanced_metrics_consistency():
    bus = EventBus()

    def handler(event: Event):
        return True

    bus.subscribe("topic", handler)
    await bus.publish("topic", Event(target_slot="slot", payload={}))

    base = bus.get_base_compatible_metrics()
    enhanced = bus.get_enhanced_metrics()

    for key, value in base.items():
        assert enhanced[f"enhanced_{key}"] == value


def test_supports_enhanced_metrics_flag():
    bus = EventBus()
    assert bus.supports_enhanced_metrics() is True


@pytest.mark.asyncio
@pytest.mark.performance
async def test_enhanced_metrics_performance_and_memory():
    bus = EventBus()

    def handler(event: Event):
        return True

    bus.subscribe("topic", handler)
    await bus.publish("topic", Event(target_slot="slot", payload={}))

    start = time.perf_counter()
    for _ in range(1000):
        bus.get_base_compatible_metrics()
    base_duration = time.perf_counter() - start

    start = time.perf_counter()
    for _ in range(1000):
        bus.get_enhanced_metrics()
    enhanced_duration = time.perf_counter() - start

    assert enhanced_duration <= base_duration * 10

    tracemalloc.start()
    bus.get_enhanced_metrics()
    _, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    assert peak < 10_000
