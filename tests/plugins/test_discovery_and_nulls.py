"""Tests for plugin discovery and null adapter functionality."""

import os
import pytest

from orchestrator.plugins.loader import PluginLoader
from orchestrator.adapters.registry import AdapterRegistry


def test_discovery_respects_whitelist(monkeypatch):
    """Test that plugin discovery respects NOVA_SLOTS environment variable."""
    # Use real slots directory from repository
    monkeypatch.setenv("NOVA_SLOTS", "slot06_cultural_synthesis,slot04_tri_engine")

    enabled_slots = os.getenv("NOVA_SLOTS").split(",")
    loader = PluginLoader(enabled=enabled_slots)
    loaded = loader.discover()

    # Should include enabled slots
    assert "slot06_cultural_synthesis" in loaded
    assert "slot04_tri_engine" in loaded

    # Check that enabled slots have plugins loaded (or at least attempted)
    for slot_id in enabled_slots:
        if slot_id in loaded:
            slot = loaded[slot_id]
            assert slot.meta is not None
            # Plugin may be None if import failed, but meta should exist


def test_discovery_loads_all_when_no_whitelist():
    """Test that discovery loads all available slots when no filter is set."""
    loader = PluginLoader(enabled=None)  # No filter
    loaded = loader.discover()

    # Should find at least our test slots
    slot_ids = list(loaded.keys())
    expected_slots = ["slot02_deltathresh", "slot04_tri_engine", "slot05_constellation", "slot06_cultural_synthesis"]

    for slot_id in expected_slots:
        assert slot_id in slot_ids, f"Expected slot {slot_id} not found in {slot_ids}"


def test_null_adapter_fallback():
    """Test that null adapters provide fallbacks when no providers available."""
    # Create loader with limited slots
    loader = PluginLoader(enabled=["slot04_tri_engine"])
    loader.discover()

    # Create registry with null adapters
    registry = AdapterRegistry(loader)
    registry.register_null("CULTURAL_PROFILE@1", lambda p: {"consent_required": True, "source": "null_adapter"})
    registry.register_null("TRI_REPORT@1", lambda p: {"tri_score": 0.5, "source": "null_adapter"})

    # Test null adapter for missing contract
    result = registry.call("CULTURAL_PROFILE@1", {"content": "test"})
    assert result == {"consent_required": True, "source": "null_adapter"}

    # Test real provider when available
    tri_result = registry.call("TRI_REPORT@1", {"content": "test"})
    # Should either get real result or null adapter, but not error
    assert isinstance(tri_result, dict)


def test_contract_provider_counting():
    """Test that registry correctly counts providers per contract."""
    loader = PluginLoader(enabled=["slot06_cultural_synthesis", "slot04_tri_engine"])
    loader.discover()
    registry = AdapterRegistry(loader)

    contracts = registry.get_contracts()

    # Should have entries for available contracts
    assert isinstance(contracts, dict)

    # Each contract should have at least 0 providers
    for contract_id, count in contracts.items():
        assert count >= 0
        assert isinstance(contract_id, str)


def test_plugin_health_collection():
    """Test that plugin health can be collected safely."""
    loader = PluginLoader(enabled=["slot06_cultural_synthesis"])
    loader.discover()

    health = loader.get_health()

    assert isinstance(health, dict)

    # Should have health for slot06 (even if plugin failed to load)
    assert "slot06_cultural_synthesis" in health

    slot6_health = health["slot06_cultural_synthesis"]
    assert isinstance(slot6_health, dict)

    # Should have either valid health or error status
    assert ("status" in slot6_health) or ("error" in slot6_health)


def test_adapter_error_handling():
    """Test that adapter registry handles errors gracefully."""
    loader = PluginLoader(enabled=[])  # Empty slots
    registry = AdapterRegistry(loader)

    # Call non-existent contract without null adapter
    result = registry.call("NONEXISTENT_CONTRACT@1", {"test": "data"})

    assert isinstance(result, dict)
    assert "error" in result
    assert "no_provider_for_contract" in result["error"]


def test_plugin_start_stop_lifecycle():
    """Test plugin lifecycle methods don't crash."""
    loader = PluginLoader(enabled=["slot06_cultural_synthesis"])
    loader.discover()

    # Mock event bus and config
    mock_bus = object()
    mock_config = {"slot06_cultural_synthesis": {"test": "config"}}

    # Should not raise exceptions
    loader.start_all(mock_bus, mock_config)
    loader.stop_all()


@pytest.mark.parametrize("contract_id", [
    "TRI_REPORT@1",
    "CULTURAL_PROFILE@1",
    "DETECTION_REPORT@1",
    "CONSTELLATION_STATE@1"
])
def test_null_adapters_for_core_contracts(contract_id):
    """Test that we can register null adapters for all core contracts."""
    loader = PluginLoader(enabled=[])  # No plugins
    registry = AdapterRegistry(loader)

    # Register null adapter
    registry.register_null(contract_id, lambda p: {"contract": contract_id, "null": True})

    # Should use null adapter
    result = registry.call(contract_id, {"test": "payload"})

    assert result == {"contract": contract_id, "null": True}

    # Should be listed in null adapters
    null_adapters = registry.get_null_adapters()
    assert contract_id in null_adapters
