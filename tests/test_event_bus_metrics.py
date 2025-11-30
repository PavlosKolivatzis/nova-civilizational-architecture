import pytest

from nova.orchestrator.core.event_bus import EventBus, Event


@pytest.mark.asyncio
async def test_event_bus_metrics_track_failures():
    bus = EventBus()

    def failing_handler(event: Event):
        raise ValueError("Test failure")

    bus.subscribe("test_event", failing_handler)

    with pytest.raises(ValueError):
        await bus.publish("test_event", Event(target_slot="slot", payload={}))

    assert bus.metrics["total_attempts"] == 1
    assert bus.metrics["failed_attempts"] == 1
    assert bus.metrics.get("successful_attempts", 0) == 0
    assert bus.metrics["published"] == 1
    assert bus.get_success_rate() == 0.0


@pytest.mark.asyncio
async def test_event_bus_metrics_track_successes():
    bus = EventBus()
    called = []

    def successful_handler(event: Event):
        called.append(event.payload)

    bus.subscribe("test_event", successful_handler)

    await bus.publish("test_event", Event(target_slot="slot", payload={}))

    assert bus.metrics["published"] == 1
    assert bus.metrics["total_attempts"] == 1
    assert bus.metrics.get("failed_attempts", 0) == 0
    assert bus.metrics["successful_attempts"] == 1
    assert bus.get_success_rate() == 1.0
