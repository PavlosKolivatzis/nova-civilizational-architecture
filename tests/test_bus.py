import asyncio
import pytest

from orchestrator.bus import EventBus


@pytest.mark.asyncio
async def test_publish_and_metrics_timeout() -> None:
    bus = EventBus(handler_timeout=0.2)
    called = []

    async def handler(payload):
        called.append(payload)

    bus.subscribe("ping", handler)

    # normal call
    await bus.publish("ping", {"x": 1})
    assert called == [{"x": 1}]
    snap = bus.snapshot()
    assert snap["events"] == 1
    assert snap["errors"] == 0

    # timeout handler
    async def slow(_):
        await asyncio.sleep(1)

    bus.subscribe("ping", slow)
    await bus.publish("ping", {})
    snap = bus.snapshot()
    assert snap["errors"] == 1
