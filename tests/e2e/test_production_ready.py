import pytest
from orchestrator.app import handle_request, monitor
pytestmark = pytest.mark.asyncio


@pytest.mark.perf
async def test_slot1_perf_guardrail():
    for i in range(10):
        await handle_request("slot1_truth_anchor", {"content": "verified"}, f"g-{i}")
    h = monitor.get_slot_health("slot1_truth_anchor")
    assert h["avg_latency_ms"] < 1000
    assert h["error_rate"] < 0.2
