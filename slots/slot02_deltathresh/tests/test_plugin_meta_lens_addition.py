"""Test meta-lens plugin integration."""

import os
import pytest
from slots.slot02_deltathresh.plugin_meta_lens_addition import _meta_lens_analyze


def test_plugin_meta_lens_enabled_smoke(monkeypatch):
    """Test meta-lens plugin when enabled."""
    monkeypatch.setenv("NOVA_ENABLE_META_LENS", "1")

    payload = {
        "text": "test content for meta-lens analysis",
        "context": {"lightclock_tick": 1234}
    }

    result = _meta_lens_analyze(payload)

    # Verify basic structure
    assert result["source_slot"] == "S2"
    assert result["schema_version"] == "1.0.0"

    # Verify meta-lens analysis
    assert "meta_lens_analysis" in result
    meta_analysis = result["meta_lens_analysis"]
    assert meta_analysis["cognitive_level"] == "synthesis"
    assert len(meta_analysis["lenses_applied"]) == 5
    assert len(meta_analysis["state_vector"]) == 6
    assert all(0.0 <= v <= 1.0 for v in meta_analysis["state_vector"])

    # Verify iteration completed
    assert "iteration" in result
    iteration = result["iteration"]
    assert iteration["epoch"] >= 1
    assert isinstance(iteration["converged"], bool)
    assert 0.0 <= iteration["residual"] <= 1.0

    # Verify integrity hash
    assert result["integrity"]["hash"].startswith("sha256:")
    assert result["integrity"]["signed_by"] == "slot01_truth_anchor"

    # Verify processing metadata
    assert "snapshots_count" in result
    assert len(result["notes"]) > 0


def test_plugin_meta_lens_disabled_smoke(monkeypatch):
    """Test meta-lens plugin when disabled."""
    monkeypatch.setenv("NOVA_ENABLE_META_LENS", "0")

    payload = {"text": "anything"}
    result = _meta_lens_analyze(payload)

    # Should return disabled stub
    assert result.get("disabled") is True
    assert result.get("reason") == "NOVA_ENABLE_META_LENS not enabled"
    assert result["source_slot"] == "S2"
    assert len(result["meta_lens_analysis"]["state_vector"]) == 6
    assert all(v == 0.0 for v in result["meta_lens_analysis"]["state_vector"])


def test_plugin_meta_lens_different_payloads():
    """Test meta-lens plugin with different payload formats."""
    os.environ["NOVA_ENABLE_META_LENS"] = "1"

    try:
        # Test string payload
        result1 = _meta_lens_analyze("simple string content")
        assert result1["source_slot"] == "S2"
        assert result1["iteration"]["epoch"] >= 1

        # Test dict with content key
        result2 = _meta_lens_analyze({"content": "dict content"})
        assert result2["source_slot"] == "S2"
        assert result2["iteration"]["epoch"] >= 1

        # Test dict with text key
        result3 = _meta_lens_analyze({"text": "dict text"})
        assert result3["source_slot"] == "S2"
        assert result3["iteration"]["epoch"] >= 1

        # All should have valid structure
        for result in [result1, result2, result3]:
            assert "meta_lens_analysis" in result
            assert "iteration" in result
            assert "integrity" in result

    finally:
        if "NOVA_ENABLE_META_LENS" in os.environ:
            del os.environ["NOVA_ENABLE_META_LENS"]


def test_plugin_meta_lens_convergence_behavior():
    """Test meta-lens convergence behavior."""
    os.environ["NOVA_ENABLE_META_LENS"] = "1"

    try:
        payload = {
            "text": "content for convergence test",
            "context": {"lightclock_tick": 5000}
        }

        result = _meta_lens_analyze(payload)

        # Check iteration details
        iteration = result["iteration"]
        assert 1 <= iteration["epoch"] <= iteration["max_iters"]
        assert iteration["alpha"] == 0.5
        assert iteration["epsilon"] == 0.02

        # Check state vector bounds
        state_vector = result["meta_lens_analysis"]["state_vector"]
        assert all(0.0 <= v <= 1.0 for v in state_vector)

        # Check frozen inputs were set
        frozen = iteration["frozen_inputs"]
        assert frozen["padel_ref"].startswith("padel_")
        assert frozen["infinity_ref"].startswith("inf_")

        # Check risk assessment
        risk = result["risk_assessment"]
        assert risk["level"] in ["low", "medium", "high", "critical"]

    finally:
        if "NOVA_ENABLE_META_LENS" in os.environ:
            del os.environ["NOVA_ENABLE_META_LENS"]


def test_plugin_meta_lens_error_handling():
    """Test meta-lens plugin error handling."""
    os.environ["NOVA_ENABLE_META_LENS"] = "1"

    try:
        # This might trigger an error in mock functions or validation
        # The plugin should handle gracefully and return error payload

        # Test with potentially problematic payload
        payload = {"text": "", "context": {}}  # Empty content
        result = _meta_lens_analyze(payload)

        # Should still return valid structure (either success or error)
        assert "source_slot" in result
        assert "meta_lens_analysis" in result
        assert "iteration" in result

        # If error occurred, should have error fields
        if "error" in result:
            assert result["risk_assessment"]["level"] == "critical"
            assert "processing_error" in result["risk_assessment"]["vectors"]

    finally:
        if "NOVA_ENABLE_META_LENS" in os.environ:
            del os.environ["NOVA_ENABLE_META_LENS"]


def test_plugin_meta_lens_schema_validation():
    """Test that plugin output matches META_LENS_REPORT@1 schema."""
    os.environ["NOVA_ENABLE_META_LENS"] = "1"

    try:
        from contracts.validators.meta_lens_validator import validate_meta_lens_report

        payload = {
            "text": "schema validation test content",
            "context": {"lightclock_tick": 2000}
        }

        result = _meta_lens_analyze(payload)

        # Should pass schema validation without exceptions
        validate_meta_lens_report(result)

    except ImportError:
        pytest.skip("Meta-lens validator not available")
    finally:
        if "NOVA_ENABLE_META_LENS" in os.environ:
            del os.environ["NOVA_ENABLE_META_LENS"]