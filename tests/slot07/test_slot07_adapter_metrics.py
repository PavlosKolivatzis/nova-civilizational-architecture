"""Smoke test for Slot7 adapter feature flag metrics integration."""

import os
import pytest


def test_slot7_adapter_exposes_flag_metrics():
    """Ensure Slot7 adapter exposes feature_flags block in metrics."""
    try:
        from nova.orchestrator.adapters.slot7_production_controls import Slot7ProductionControlsAdapter
    except Exception:
        pytest.skip("Slot7 adapter not available")

    # Ensure clean environment for consistent test
    os.environ.pop("NOVA_ENABLE_TRI_LINK", None)
    os.environ.pop("NOVA_ENABLE_LIFESPAN", None)
    os.environ.pop("NOVA_USE_SHARED_HASH", None)

    adapter = Slot7ProductionControlsAdapter()
    if not getattr(adapter, "available", True):
        pytest.skip("Slot7 not available")

    # Process request to get metrics
    result = adapter.process({"action": "get_metrics"})
    assert isinstance(result, dict), "Slot7 should return dict response"

    # Check for feature_flags in the result structure
    # Could be directly in result or nested under metrics/result
    feature_flags = None
    if "feature_flags" in result:
        feature_flags = result["feature_flags"]
    elif "result" in result and isinstance(result["result"], dict):
        if "feature_flags" in result["result"]:
            feature_flags = result["result"]["feature_flags"]
        elif "metrics" in result["result"] and isinstance(result["result"]["metrics"], dict):
            if "feature_flags" in result["result"]["metrics"]:
                feature_flags = result["result"]["metrics"]["feature_flags"]
    elif "metrics" in result and isinstance(result["metrics"], dict):
        if "feature_flags" in result["metrics"]:
            feature_flags = result["metrics"]["feature_flags"]

    assert feature_flags is not None, "feature_flags block missing from Slot7 response"
    assert isinstance(feature_flags, dict), "feature_flags should be a dict"

    # Verify required keys are present
    expected_keys = {
        "tri_link_enabled",
        "lifespan_enabled",
        "shared_hash_enabled",
        "shared_hash_available",
        "effective_hash_method"
    }
    assert set(feature_flags.keys()) >= expected_keys, f"Missing keys in feature_flags: {expected_keys - set(feature_flags.keys())}"

    # Verify value types
    assert isinstance(feature_flags["tri_link_enabled"], bool)
    assert isinstance(feature_flags["lifespan_enabled"], bool)
    assert isinstance(feature_flags["shared_hash_enabled"], bool)
    assert isinstance(feature_flags["shared_hash_available"], bool)
    assert isinstance(feature_flags["effective_hash_method"], str)
    assert feature_flags["effective_hash_method"] in {"shared_blake2b", "fallback_sha256"}


@pytest.mark.health
def test_slot7_adapter_metrics_health_check():
    """Lightweight health check for Slot7 adapter."""
    try:
        from nova.orchestrator.adapters.slot7_production_controls import Slot7ProductionControlsAdapter
        adapter = Slot7ProductionControlsAdapter()
        # Just verify adapter can be created and has expected interface
        assert hasattr(adapter, "process")
        assert hasattr(adapter, "available")
    except Exception:
        pytest.skip("Slot7 adapter not available")


@pytest.mark.health
def test_slot7_adapter_includes_slot6_p95():
    """Test that Slot7 adapter exposes Slot6 p95 residual risk."""
    try:
        from nova.orchestrator.adapters.slot7_production_controls import Slot7ProductionControlsAdapter
    except Exception:
        pytest.skip("Slot7 adapter not available")

    # Prime Slot6 so p95 is not None
    from nova.orchestrator.metrics import get_slot6_metrics
    m = get_slot6_metrics()
    # ensure clean window (no cross-test residue)
    m.reset()
    for v in (0.1, 0.4, 0.7, 0.9):
        m.record_decision("approved", 0.8, v)

    ad = Slot7ProductionControlsAdapter()
    out = ad.process({"action": "get_metrics"})

    # Navigate to the metrics structure
    result = out.get("result", {})
    metrics = result.get("metrics", {})
    feature_flags = metrics.get("feature_flags", {})

    # Check that slot6_p95_residual_risk is present and valid
    p95 = feature_flags.get("slot6_p95_residual_risk")
    if p95 is None:
        # accept nested location as well
        p95 = (metrics.get("slot6") or {}).get("p95_residual_risk")
    assert p95 is not None, "slot6_p95_residual_risk should be present in feature_flags"
    assert 0.1 <= p95 <= 0.9, f"p95={p95} should be within expected range"
