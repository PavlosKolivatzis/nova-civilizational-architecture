"""Smoke tests for plugin system."""

import importlib
import types
from orchestrator.plugins.loader import PluginLoader


def test_plugins_package_import_safe():
    """Test that plugins package imports without errors."""
    pkg = importlib.import_module("orchestrator.plugins")
    assert isinstance(pkg, types.ModuleType)


def test_plugin_loader_import():
    """Test that PluginLoader can be imported."""
    from orchestrator.plugins import PluginLoader
    assert PluginLoader is not None


def test_plugin_discovery_returns_dict():
    """Test that plugin discovery returns a dict structure."""
    loader = PluginLoader()
    plugins = loader.discover()
    assert isinstance(plugins, dict)


def test_plugin_loader_initialization():
    """Test that PluginLoader initializes correctly."""
    loader = PluginLoader(enabled=["slot06_cultural_synthesis"])
    assert loader is not None
    
    # Should be able to discover plugins
    loaded = loader.discover()
    assert isinstance(loaded, dict)


def test_plugin_health_collection_safe():
    """Test that plugin health collection doesn't crash."""
    loader = PluginLoader()
    loader.discover()
    
    health = loader.get_health()
    assert isinstance(health, dict)