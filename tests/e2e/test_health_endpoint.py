"""
Tests for health endpoint functionality.
"""
import pytest

pytestmark = pytest.mark.health
from unittest.mock import MagicMock
from orchestrator.health import health_payload, collect_slot_health


@pytest.fixture
def mock_components():
    """Mock components for health testing."""
    slot_registry = {"slot1": lambda: None, "slot6": lambda: None}
    monitor = MagicMock()
    monitor.get_slot_health.return_value = {"status": "healthy", "latency_ms": 50}
    router = MagicMock()
    router.latency_threshold_ms = 1000.0
    router.error_threshold = 0.2
    return slot_registry, monitor, router


def test_health_payload_shapes(mock_components):
    """Test health payload contains expected structure."""
    slot_registry, monitor, router = mock_components
    payload = health_payload(slot_registry, monitor, router)

    assert "slots" in payload
    assert "router_thresholds" in payload
    assert "circuit_breaker" in payload
    assert isinstance(payload["slots"], dict)
    assert len(payload["slots"]) == 2


def test_collect_slot_health(mock_components):
    """Test slot health collection."""
    slot_registry, monitor, _ = mock_components
    health_data = collect_slot_health(slot_registry, monitor)

    assert "slot1" in health_data
    assert "slot6" in health_data
    assert health_data["slot1"]["status"] == "healthy"
