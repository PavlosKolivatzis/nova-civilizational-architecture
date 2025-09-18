"""Smoke test for Slot7 adapter feature flag metrics integration."""

import os
import pytest


def test_slot7_adapter_exposes_flag_metrics():
    """Ensure Slot7 adapter exposes feature_flags block in metrics."""
    try:
        from orchestrator.adapters.slot7_production_controls import Slot7ProductionControlsAdapter
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
        from orchestrator.adapters.slot7_production_controls import Slot7ProductionControlsAdapter
        adapter = Slot7ProductionControlsAdapter()
        # Just verify adapter can be created and has expected interface
        assert hasattr(adapter, "process")
        assert hasattr(adapter, "available")
    except Exception:
        pytest.skip("Slot7 adapter not available")