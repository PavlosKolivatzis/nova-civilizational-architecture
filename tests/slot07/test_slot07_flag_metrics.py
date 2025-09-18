"""Tests for Slot7 Phase-2 feature flag metrics."""

import os
import pytest


def test_flag_metrics_defaults_off(monkeypatch):
    """Test flag metrics with all flags disabled (default state)."""
    from slots.slot07_production_controls.flag_metrics import get_flag_state_metrics

    # Clear all flag environment variables
    for k in ("NOVA_ENABLE_TRI_LINK", "NOVA_ENABLE_LIFESPAN", "NOVA_USE_SHARED_HASH"):
        monkeypatch.delenv(k, raising=False)

    metrics = get_flag_state_metrics()

    assert metrics["tri_link_enabled"] is False
    assert metrics["lifespan_enabled"] is False
    assert metrics["shared_hash_enabled"] is False
    assert metrics["effective_hash_method"] in {"shared_blake2b", "fallback_sha256"}
    assert isinstance(metrics["shared_hash_available"], bool)


def test_flag_metrics_truthy_variants(monkeypatch):
    """Test that various truthy values enable flags."""
    from slots.slot07_production_controls.flag_metrics import get_flag_state_metrics

    for val in ["1", "true", "TRUE", "yes", "YES", "on", "On"]:
        monkeypatch.setenv("NOVA_ENABLE_TRI_LINK", val)
        monkeypatch.setenv("NOVA_ENABLE_LIFESPAN", val)
        monkeypatch.setenv("NOVA_USE_SHARED_HASH", val)

        metrics = get_flag_state_metrics()

        assert metrics["tri_link_enabled"] is True
        assert metrics["lifespan_enabled"] is True
        assert metrics["shared_hash_enabled"] is True


def test_flag_metrics_falsy_variants(monkeypatch):
    """Test that falsy values disable flags."""
    from slots.slot07_production_controls.flag_metrics import get_flag_state_metrics

    for val in ["0", "false", "FALSE", "no", "off", "invalid", ""]:
        monkeypatch.setenv("NOVA_ENABLE_TRI_LINK", val)
        monkeypatch.setenv("NOVA_ENABLE_LIFESPAN", val)
        monkeypatch.setenv("NOVA_USE_SHARED_HASH", val)

        metrics = get_flag_state_metrics()

        assert metrics["tri_link_enabled"] is False
        assert metrics["lifespan_enabled"] is False
        assert metrics["shared_hash_enabled"] is False


def test_effective_hash_method(monkeypatch):
    """Test effective hash method selection based on availability and flag."""
    from slots.slot07_production_controls.flag_metrics import get_flag_state_metrics

    # Test with shared hash enabled
    monkeypatch.setenv("NOVA_USE_SHARED_HASH", "1")
    metrics_enabled = get_flag_state_metrics()

    # Should be shared_blake2b if available, otherwise fallback
    assert metrics_enabled["effective_hash_method"] in {"shared_blake2b", "fallback_sha256"}

    # Test with shared hash disabled
    monkeypatch.setenv("NOVA_USE_SHARED_HASH", "0")
    metrics_disabled = get_flag_state_metrics()

    # Should always be fallback when flag is disabled
    assert metrics_disabled["effective_hash_method"] == "fallback_sha256"


def test_comprehensive_metrics_includes_flags():
    """Test that comprehensive metrics includes feature flag states."""
    from slots.slot07_production_controls.production_control_engine import ProductionControlEngine

    engine = ProductionControlEngine()
    metrics = engine.get_comprehensive_metrics()

    # Verify feature_flags section exists
    assert "feature_flags" in metrics
    flag_metrics = metrics["feature_flags"]

    # Verify all expected keys are present
    expected_keys = {
        "tri_link_enabled",
        "lifespan_enabled",
        "shared_hash_enabled",
        "shared_hash_available",
        "effective_hash_method"
    }
    assert set(flag_metrics.keys()) == expected_keys

    # Verify types
    assert isinstance(flag_metrics["tri_link_enabled"], bool)
    assert isinstance(flag_metrics["lifespan_enabled"], bool)
    assert isinstance(flag_metrics["shared_hash_enabled"], bool)
    assert isinstance(flag_metrics["shared_hash_available"], bool)
    assert isinstance(flag_metrics["effective_hash_method"], str)


def test_flag_states_with_mixed_values(monkeypatch):
    """Test individual flag states with mixed values."""
    from slots.slot07_production_controls.flag_metrics import get_flag_state_metrics

    monkeypatch.setenv("NOVA_ENABLE_TRI_LINK", "1")
    monkeypatch.setenv("NOVA_ENABLE_LIFESPAN", "0")
    monkeypatch.setenv("NOVA_USE_SHARED_HASH", "true")

    metrics = get_flag_state_metrics()

    assert metrics["tri_link_enabled"] is True
    assert metrics["lifespan_enabled"] is False
    assert metrics["shared_hash_enabled"] is True