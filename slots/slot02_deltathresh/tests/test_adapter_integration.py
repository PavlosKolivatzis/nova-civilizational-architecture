"""Test adapter integration with real and mock adapters."""

import pytest
from slots.slot02_deltathresh.adapter_integration_patch import create_real_adapter_functions, create_mock_functions


class MockAdapterRegistry:
    """Mock adapter registry for testing real adapter functions."""

    def __init__(self, responses=None):
        self.responses = responses or {}
        self.calls = []

    def call(self, contract_id, payload):
        """Mock adapter registry call."""
        self.calls.append((contract_id, payload))
        return self.responses.get(contract_id, {})


def test_create_mock_functions():
    """Test mock function creation."""
    tri_fn, const_fn, culture_fn, distort_fn, emo_fn = create_mock_functions()

    # Test mock TRI function
    tri_result = tri_fn({"meta_lens_analysis": {"state_vector": [0.5] * 6}})
    assert tri_result["resonance_cross"] == 0.7
    assert tri_result["coherence"] == 0.8

    # Test mock constellation function
    const_result = const_fn({"meta_lens_analysis": {"state_vector": [0.5] * 6}})
    assert const_result["coordination_hint"] == "stable"
    assert const_result["topology"] == "connected"

    # Test mock culture function
    culture_result = culture_fn({}, {}, {})
    assert culture_result["synthesis_confidence"] == 0.85
    assert culture_result["risk_overall"] == 0.25
    assert len(culture_result["bias_markers"]) == 1

    # Test mock distortion function
    distort_result = distort_fn({"iteration": {"frozen_inputs": {"infinity_ref": "test"}}})
    assert distort_result["overall_score"] == 0.15
    assert len(distort_result["patterns"]) == 1

    # Test mock emotion function
    emo_result = emo_fn({"iteration": {"frozen_inputs": {"padel_ref": "test"}}})
    assert emo_result["volatility"] == 0.2
    assert emo_result["stability"] == 0.8


def test_create_real_adapter_functions_with_no_registry():
    """Test that real adapter functions fall back to mocks when no registry provided."""
    content = "test content"
    context = {"adapter_registry": None}

    tri_fn, const_fn, culture_fn, distort_fn, emo_fn = create_real_adapter_functions(content, context)

    # Should return mock functions when no registry
    tri_result = tri_fn({"meta_lens_analysis": {"state_vector": [0.5] * 6}})
    assert tri_result["resonance_cross"] == 0.7  # Mock value


def test_create_real_adapter_functions_with_registry():
    """Test real adapter functions with mock registry."""
    # Set up mock registry with responses
    mock_responses = {
        "TRI_REPORT@1": {
            "cross_family_resonance": 0.85,
            "coherence": 0.9,
            "stability": 0.8
        },
        "CONSTELLATION_REPORT@1": {
            "coordination_hint": "optimal",
            "topology_type": "mesh",
            "phase_coherence": 0.95
        },
        "CULTURAL_PROFILE@1": {
            "synthesis_confidence": 0.92,
            "risk_assessment": {"overall": 0.15},
            "historical_context": "Test historical context",
            "bias_markers": ["test_bias1", "test_bias2"],
            "risk_vectors": ["test_vector"],
            "mitigation_suggestions": ["test_mitigation"]
        },
        "DETECTION_REPORT@1": {
            "distortion_score": 0.05,
            "patterns_detected": [{"id": "real-1", "name": "real_pattern"}],
            "confidence": 0.95,
            "threat_level": "minimal"
        },
        "EMOTION_REPORT@1": {
            "volatility": 0.1,
            "stability": 0.95,
            "emotional_state": "calm"
        }
    }

    mock_registry = MockAdapterRegistry(mock_responses)
    content = "test content"
    context = {"adapter_registry": mock_registry}

    tri_fn, const_fn, culture_fn, distort_fn, emo_fn = create_real_adapter_functions(content, context)

    # Test TRI function with real adapter
    tri_result = tri_fn({"meta_lens_analysis": {"state_vector": [0.5] * 6}})
    assert tri_result["resonance_cross"] == 0.85  # Real adapter value
    assert tri_result["coherence"] == 0.9
    assert tri_result["stability"] == 0.8

    # Test constellation function
    const_result = const_fn({"meta_lens_analysis": {"state_vector": [0.5] * 6}})
    assert const_result["coordination_hint"] == "optimal"
    assert const_result["topology"] == "mesh"
    assert const_result["phase_coherence"] == 0.95

    # Test culture function
    culture_result = culture_fn({}, {}, {})
    assert culture_result["synthesis_confidence"] == 0.92
    assert culture_result["risk_overall"] == 0.15
    assert culture_result["historical_context"] == "Test historical context"
    assert "test_bias1" in culture_result["bias_markers"]

    # Test distortion function
    distort_result = distort_fn({"iteration": {"frozen_inputs": {"infinity_ref": "test"}}})
    assert distort_result["overall_score"] == 0.05
    assert distort_result["threat_level"] == "minimal"

    # Test emotion function
    emo_result = emo_fn({"iteration": {"frozen_inputs": {"padel_ref": "test"}}})
    assert emo_result["volatility"] == 0.1
    assert emo_result["stability"] == 0.95
    assert emo_result["emotional_state"] == "calm"

    # Verify registry was called correctly (single call test)
    assert len(mock_registry.calls) == 5
    contract_ids = [call[0] for call in mock_registry.calls]
    assert "TRI_REPORT@1" in contract_ids
    assert "CONSTELLATION_REPORT@1" in contract_ids
    assert "CULTURAL_PROFILE@1" in contract_ids
    assert "DETECTION_REPORT@1" in contract_ids
    assert "EMOTION_REPORT@1" in contract_ids


def test_real_adapter_functions_error_handling():
    """Test graceful error handling in real adapter functions."""
    # Registry that raises exceptions
    class ErrorRegistry:
        def call(self, contract_id, payload):
            raise Exception(f"Adapter {contract_id} failed")

    error_registry = ErrorRegistry()
    content = "test content"
    context = {"adapter_registry": error_registry}

    tri_fn, const_fn, culture_fn, distort_fn, emo_fn = create_real_adapter_functions(content, context)

    # Test error handling
    tri_result = tri_fn({"meta_lens_analysis": {"state_vector": [0.5] * 6}})
    assert tri_result["resonance_cross"] == 0.5  # Fallback value
    assert "error" in tri_result

    const_result = const_fn({"meta_lens_analysis": {"state_vector": [0.5] * 6}})
    assert const_result["coordination_hint"] == "degraded"
    assert "error" in const_result

    culture_result = culture_fn({}, {}, {})
    assert culture_result["synthesis_confidence"] == 0.0  # Conservative fallback
    assert culture_result["risk_overall"] == 1.0  # Conservative fallback
    assert "Error in cultural analysis" in culture_result["historical_context"]

    distort_result = distort_fn({"iteration": {"frozen_inputs": {"infinity_ref": "test"}}})
    assert distort_result["overall_score"] == 0.5  # Conservative fallback
    assert "error" in distort_result

    emo_result = emo_fn({"iteration": {"frozen_inputs": {"padel_ref": "test"}}})
    assert emo_result["volatility"] == 0.5  # Conservative fallback
    assert "error" in emo_result


def test_integration_with_meta_lens_plugin(monkeypatch):
    """Test integration with meta-lens plugin - stable epoch testing."""
    import os, importlib, sys

    # Set test env BEFORE import
    monkeypatch.setenv("META_LENS_MAX_ITERS", "3")
    monkeypatch.setenv("META_LENS_EPSILON", "0.0")  # Never converges early
    monkeypatch.setenv("META_LENS_ALPHA", "0.5")  # Keep damping constant
    monkeypatch.setenv("NOVA_ENABLE_META_LENS", "1")
    monkeypatch.setenv("NOVA_META_LENS_TEST_ENFORCE_REAL", "1")

    # Re-import fresh modules in this env
    for m in [
        "slots.slot02_deltathresh.adapter_integration_patch",
        "slots.slot02_deltathresh.meta_lens_processor",
        "slots.slot02_deltathresh.plugin_meta_lens_addition",
    ]:
        if m in sys.modules:
            del sys.modules[m]
    import slots.slot02_deltathresh.plugin_meta_lens_addition as plugin

    try:
        # Test with mock registry that provides custom responses
        mock_responses = {
            "TRI_REPORT@1": {"cross_family_resonance": 0.9, "coherence": 0.95},
            "CONSTELLATION_REPORT@1": {"coordination_hint": "excellent", "topology_type": "optimized"},
            "CULTURAL_PROFILE@1": {"synthesis_confidence": 0.98, "risk_assessment": {"overall": 0.05}},
            "DETECTION_REPORT@1": {"distortion_score": 0.02, "confidence": 0.99},
            "EMOTION_REPORT@1": {"volatility": 0.05, "stability": 0.98}
        }

        mock_registry = MockAdapterRegistry(mock_responses)

        payload = {
            "text": "Integration test content",
            "context": {
                "adapter_registry": mock_registry,
                "lightclock_tick": 2000
            }
        }

        result = plugin._meta_lens_analyze(payload)

        # Verify successful processing
        assert result["source_slot"] == "S2"
        assert result["meta_lens_analysis"]["cognitive_level"] == "synthesis"
        assert result["iteration"]["epoch"] == 3  # Forced 3 iterations
        assert result["lightclock_tick"] == 2000

        # Verify real adapters were called in full epochs (5 calls per epoch)
        assert len(mock_registry.calls) % 5 == 0
        assert len(mock_registry.calls) >= 5
        assert len(mock_registry.calls) == 15  # 3 iterations × 5 adapters

        # Verify real adapters were used
        assert any("real_adapters" in str(n) for n in result.get("notes", []))

    finally:
        # Clean up environment
        pass  # monkeypatch handles cleanup automatically


def test_integration_with_natural_convergence(monkeypatch):
    """Test integration with natural convergence (variable epoch count)."""
    import os, importlib, sys

    # Set test env BEFORE import
    monkeypatch.setenv("NOVA_ENABLE_META_LENS", "1")
    monkeypatch.setenv("NOVA_META_LENS_TEST_ENFORCE_REAL", "1")

    # Re-import fresh modules in this env
    for m in [
        "slots.slot02_deltathresh.adapter_integration_patch",
        "slots.slot02_deltathresh.meta_lens_processor",
        "slots.slot02_deltathresh.plugin_meta_lens_addition",
    ]:
        if m in sys.modules:
            del sys.modules[m]
    import slots.slot02_deltathresh.plugin_meta_lens_addition as plugin

    try:
        # Mock registry with stable responses that should converge quickly
        mock_responses = {
            "TRI_REPORT@1": {"cross_family_resonance": 0.5, "coherence": 0.5},
            "CONSTELLATION_REPORT@1": {"coordination_hint": "stable", "topology_type": "connected"},
            "CULTURAL_PROFILE@1": {"synthesis_confidence": 0.5, "risk_assessment": {"overall": 0.0}},
            "DETECTION_REPORT@1": {"distortion_score": 0.0, "confidence": 0.5},
            "EMOTION_REPORT@1": {"volatility": 0.0, "stability": 1.0}
        }

        mock_registry = MockAdapterRegistry(mock_responses)

        payload = {
            "text": "Stable convergence test",
            "context": {
                "adapter_registry": mock_registry,
                "lightclock_tick": 3000
            }
        }

        result = plugin._meta_lens_analyze(payload)

        # Verify successful processing with natural convergence
        assert result["source_slot"] == "S2"
        assert result["iteration"]["epoch"] >= 1
        assert result["iteration"]["epoch"] <= 3

        # Verify adapters were called in complete epochs only
        assert len(mock_registry.calls) % 5 == 0
        assert len(mock_registry.calls) >= 5

        # Verify real adapters were used
        assert any("real_adapters" in str(n) for n in result.get("notes", []))

    finally:
        # monkeypatch handles cleanup automatically
        pass