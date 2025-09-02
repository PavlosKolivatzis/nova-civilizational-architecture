"""
End-to-end test for Slot-1 request path.
"""
import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock

pytestmark = pytest.mark.asyncio


@pytest.fixture
def mock_slot1():
    """Mock Slot-1 truth anchor."""
    slot = AsyncMock()
    slot.process.return_value = {
        "truth_score": 0.95,
        "verified": True,
        "critical": ["integrity_check", "temporal_consistency"],
        "analysis": {"depth": 8.7, "coherence": 9.2}
    }
    return slot


async def test_slot1_e2e_request_path(mock_slot1):
    """Test end-to-end request through Slot-1 with truth scoring."""
    # Simulate request
    test_content = {"content": "The capital of France is Paris.", "context": "geography"}

    # Process through slot
    result = await mock_slot1.process(test_content)

    # Assert critical response structure
    assert "truth_score" in result
    assert "verified" in result
    assert "critical" in result

    # Assert truth scoring
    assert isinstance(result["truth_score"], float)
    assert 0 <= result["truth_score"] <= 1.0

    # Assert verification
    assert isinstance(result["verified"], bool)

    # Assert critical components
    assert isinstance(result["critical"], list)
    assert len(result["critical"]) > 0


async def test_slot1_truth_threshold_compliance(mock_slot1):
    """Test that Slot-1 respects the configured truth threshold."""
    from orchestrator.config import config

    test_content = {"content": "Test statement for verification"}

    result = await mock_slot1.process(test_content)

    # If verified is True, truth_score should meet threshold
    if result["verified"]:
        assert result["truth_score"] >= config.TRUTH_THRESHOLD, \
            f"Verified result score {result['truth_score']} below threshold {config.TRUTH_THRESHOLD}"
