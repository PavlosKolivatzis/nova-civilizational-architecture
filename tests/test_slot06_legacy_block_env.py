"""Test legacy import blocking via NOVA_BLOCK_LEGACY_SLOT6 environment variable."""

import importlib
import pytest


def test_legacy_import_blocked(monkeypatch):
    """Test that NOVA_BLOCK_LEGACY_SLOT6=1 blocks legacy imports."""
    # Clear module cache first
    module_name = "nova.slots.slot06_cultural_synthesis.multicultural_truth_synthesis"
    if module_name in importlib.sys.modules:
        del importlib.sys.modules[module_name]
    
    monkeypatch.setenv("NOVA_BLOCK_LEGACY_SLOT6", "1")
    
    with pytest.raises(ImportError, match="Legacy Slot6 API is disabled"):
        importlib.import_module("nova.slots.slot06_cultural_synthesis.multicultural_truth_synthesis")


def test_legacy_import_blocked_truthy_values(monkeypatch):
    """Test that various truthy values block legacy imports."""
    truthy_values = ["1", "true", "TRUE", "yes", "YES", "on", "ON"]
    
    for value in truthy_values:
        monkeypatch.setenv("NOVA_BLOCK_LEGACY_SLOT6", value)
        
        with pytest.raises(ImportError, match="Legacy Slot6 API is disabled"):
            importlib.import_module("nova.slots.slot06_cultural_synthesis.multicultural_truth_synthesis")
        
        # Clear the module from cache to test next value
        module_name = "nova.slots.slot06_cultural_synthesis.multicultural_truth_synthesis"
        if module_name in importlib.sys.modules:
            del importlib.sys.modules[module_name]


def test_legacy_import_allowed_falsy_values(monkeypatch):
    """Test that falsy values allow legacy imports (with deprecation warning)."""
    falsy_values = ["", "0", "false", "FALSE", "no", "NO", "off", "OFF"]
    
    for value in falsy_values:
        monkeypatch.setenv("NOVA_BLOCK_LEGACY_SLOT6", value)
        
        # Clear module from cache first
        module_name = "nova.slots.slot06_cultural_synthesis.multicultural_truth_synthesis"
        if module_name in importlib.sys.modules:
            del importlib.sys.modules[module_name]
        
        # Should succeed (with deprecation warning)
        with pytest.warns(DeprecationWarning, match="multicultural_truth_synthesis.*is deprecated"):
            importlib.import_module("nova.slots.slot06_cultural_synthesis.multicultural_truth_synthesis")


def test_legacy_import_allowed_no_env_var(monkeypatch):
    """Test that missing environment variable allows legacy imports."""
    monkeypatch.delenv("NOVA_BLOCK_LEGACY_SLOT6", raising=False)
    
    # Clear module from cache
    module_name = "nova.slots.slot06_cultural_synthesis.multicultural_truth_synthesis"
    if module_name in importlib.sys.modules:
        del importlib.sys.modules[module_name]
    
    # Should succeed (with deprecation warning)
    with pytest.warns(DeprecationWarning, match="multicultural_truth_synthesis.*is deprecated"):
        importlib.import_module("nova.slots.slot06_cultural_synthesis.multicultural_truth_synthesis")