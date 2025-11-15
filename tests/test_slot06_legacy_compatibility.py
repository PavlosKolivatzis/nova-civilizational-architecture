"""Tests for Slot 6 legacy compatibility layer."""

import json
import os
import warnings
import pytest
from collections.abc import Mapping


def _env_truthy(name: str) -> bool:
    """Check if environment variable is set to a truthy value."""
    v = os.getenv(name, "")
    return v.strip() == "1"


# Skip all legacy tests if legacy imports are blocked
pytestmark = pytest.mark.skipif(
    _env_truthy("NOVA_BLOCK_LEGACY_SLOT6"),
    reason="Legacy Slot6 API blocked by NOVA_BLOCK_LEGACY_SLOT6"
)

# Conditional imports to avoid ImportError during test collection
if not _env_truthy("NOVA_BLOCK_LEGACY_SLOT6"):
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", DeprecationWarning)
        from nova.slots.slot06_cultural_synthesis.multicultural_truth_synthesis import (
            ProfileWrapper,
            AdaptiveSynthesisEngine,
            MulticulturalTruthSynthesisAdapter,
        )
else:
    # Define stubs for when legacy is blocked
    ProfileWrapper = None
    AdaptiveSynthesisEngine = None
    MulticulturalTruthSynthesisAdapter = None


def test_profile_wrapper_is_mapping_and_attr_access():
    """Test ProfileWrapper behaves as both Mapping and supports attribute access."""

    # Test with CI-expected data
    data = {
        "adaptation_effectiveness": 0.42,
        "principle_preservation_score": 0.85,
        "residual_risk": 0.15,
        "x": 1
    }
    wrapper = ProfileWrapper(data)

    # Test attribute access (CI requirement)
    assert wrapper.x == 1
    assert wrapper.adaptation_effectiveness == 0.42
    assert wrapper.principle_preservation_score == 0.85

    # Test dict-style access
    assert wrapper["x"] == 1
    assert wrapper["adaptation_effectiveness"] == 0.42

    # Test Mapping interface
    assert isinstance(wrapper, Mapping)
    assert len(wrapper) >= 4  # Original data + any defaults
    assert list(wrapper)  # Should be iterable
    assert "x" in wrapper
    assert "adaptation_effectiveness" in wrapper

    # Test serialization compatibility
    dict_data = wrapper.to_dict()
    json_str = json.dumps(dict_data)  # Should not raise
    assert "adaptation_effectiveness" in json_str

    # Test get method
    assert wrapper.get("x") == 1
    assert wrapper.get("missing", "default") == "default"


def test_profile_wrapper_conservative_defaults():
    """Test ProfileWrapper only adds defaults when missing."""

    # Test with missing keys - should get conservative defaults
    empty_data = {"custom": "value"}
    wrapper = ProfileWrapper(empty_data)

    assert wrapper.adaptation_effectiveness == 0.0  # Conservative default
    assert wrapper.principle_preservation_score == 0.0  # Conservative default
    assert wrapper.residual_risk == 1.0  # Conservative (high risk) default
    assert wrapper.custom == "value"  # Original data preserved

    # Test with existing keys - should NOT override
    existing_data = {
        "adaptation_effectiveness": 0.75,
        "principle_preservation_score": 0.90,
        "residual_risk": 0.10
    }
    wrapper = ProfileWrapper(existing_data)

    assert wrapper.adaptation_effectiveness == 0.75  # Original preserved
    assert wrapper.principle_preservation_score == 0.90  # Original preserved
    assert wrapper.residual_risk == 0.10  # Original preserved


def test_legacy_module_returns_wrapper():
    """Test legacy module returns ProfileWrapper with both access patterns."""

    engine = AdaptiveSynthesisEngine()
    adapter = MulticulturalTruthSynthesisAdapter(engine)

    # Test the CI call pattern
    profile = adapter.analyze_cultural_context('TestInstitution', {'region': 'EU'})

    # Test both access patterns work
    effectiveness_attr = profile.adaptation_effectiveness
    effectiveness_dict = profile["adaptation_effectiveness"]
    assert effectiveness_attr == effectiveness_dict

    # Test it's a proper wrapper
    assert hasattr(profile, "to_dict")
    assert hasattr(profile, "get")
    assert isinstance(profile, Mapping)


def test_legacy_deprecation_warning():
    """Test that importing legacy module shows deprecation warning."""
    import warnings
    import sys

    # Clear module cache to ensure warning fires
    module_name = 'nova.slots.slot06_cultural_synthesis.multicultural_truth_synthesis'
    if module_name in sys.modules:
        del sys.modules[module_name]

    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        # Re-import the module to trigger deprecation warning
        import importlib
        importlib.import_module(module_name)

        # Should have at least one deprecation warning
        assert len(w) >= 1
        assert any(issubclass(warning.category, DeprecationWarning) for warning in w)
        assert any("multicultural_truth_synthesis" in str(warning.message) for warning in w)


def test_profile_wrapper_attribute_error():
    """Test ProfileWrapper raises AttributeError for missing attributes."""

    wrapper = ProfileWrapper({"existing": "value"})

    # Should work for existing
    assert wrapper.existing == "value"

    # Should raise AttributeError for missing (not KeyError)
    with pytest.raises(AttributeError):
        _ = wrapper.nonexistent_attribute
