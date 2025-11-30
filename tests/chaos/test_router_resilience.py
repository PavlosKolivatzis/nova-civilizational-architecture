"""
Chaos engineering tests for router resilience.
"""
from unittest.mock import MagicMock
from nova.orchestrator.core.router import AdaptiveRouter


def test_router_chooses_fallback_when_slow():
    """Test router selects fallback when primary slot is slow."""
    mon = MagicMock()
    mon.get_slot_health.return_value = {"avg_latency_ms": 1500.0, "error_rate": 0.0}

    r = AdaptiveRouter(mon, latency_threshold_ms=1000.0, error_threshold=1.0)
    r.fallback_map = {"slot6": "slot6_fallback"}

    routed = r.get_route("slot6", original_timeout=2.0)
    if isinstance(routed, tuple):
        slot, _ = routed
    else:
        slot = routed

    assert slot == "slot6_fallback", f"Expected slot6_fallback, got {slot}"


def test_router_uses_primary_when_healthy():
    """Test router uses primary slot when it's healthy."""
    mon = MagicMock()
    mon.get_slot_health.return_value = {"avg_latency_ms": 150.0, "error_rate": 0.0}

    r = AdaptiveRouter(mon, latency_threshold_ms=1000.0, error_threshold=1.0)
    r.fallback_map = {"slot6": "slot6_fallback"}

    routed = r.get_route("slot6", original_timeout=2.0)
    if isinstance(routed, tuple):
        slot, _ = routed
    else:
        slot = routed

    assert slot == "slot6", f"Expected slot6, got {slot}"


def test_router_handles_missing_fallback():
    """Test router behavior when fallback is not available."""
    mon = MagicMock()
    mon.get_slot_health.return_value = {"avg_latency_ms": 1500.0, "error_rate": 0.0}

    r = AdaptiveRouter(mon, latency_threshold_ms=1000.0, error_threshold=1.0)
    r.fallback_map = {}  # No fallbacks configured

    routed = r.get_route("slot6", original_timeout=2.0)
    if isinstance(routed, tuple):
        slot, _ = routed
    else:
        slot = routed

    # Should still use primary even when unhealthy if no fallback
    assert slot == "slot6", f"Expected slot6, got {slot}"
