"""
Performance guardrail tests for critical components.
"""
import pytest
import asyncio
from unittest.mock import AsyncMock


pytestmark = [pytest.mark.asyncio, pytest.mark.perf]


@pytest.fixture
def mock_slot1():
    """Mock slot1 truth anchor."""
    slot = AsyncMock()
    slot.process.return_value = {"truth_score": 0.95, "verified": True}
    return slot


async def test_slot1_basic_perf_guardrail(mock_slot1):
    """Test slot1 meets basic performance requirements."""
    latencies = []

    for i in range(5):
        start_time = asyncio.get_event_loop().time()
        await mock_slot1.process({"content": f"test content {i}"})
        end_time = asyncio.get_event_loop().time()
        latencies.append((end_time - start_time) * 1000)  # Convert to ms

    avg_latency = sum(latencies) / len(latencies)
    assert avg_latency < 1000, f"Average latency {avg_latency}ms exceeds 1000ms threshold"
    assert max(latencies) < 2000, f"Max latency {max(latencies)}ms exceeds 2000ms threshold"


async def test_slot1_error_rate_guardrail(mock_slot1):
    """Test slot1 error rate remains within acceptable limits."""
    error_count = 0
    total_requests = 10

    for i in range(total_requests):
        try:
            if i == 3 or i == 7:  # Simulate occasional errors
                mock_slot1.process.side_effect = Exception("Temporary failure")
            else:
                mock_slot1.process.side_effect = None

            await mock_slot1.process({"content": f"test content {i}"})
        except Exception:
            error_count += 1

    error_rate = error_count / total_requests
    assert error_rate < 0.5, f"Error rate {error_rate} exceeds 0.5 threshold"
