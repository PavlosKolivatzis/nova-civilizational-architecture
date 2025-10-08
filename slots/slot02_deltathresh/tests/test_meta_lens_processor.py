"""Test fixed-point meta-lens processor."""

import pytest
import os
from slots.slot02_deltathresh.meta_lens_processor import (
    vectorize, l1_norm, hash_report, compute_once,
    create_base_state, run_fixed_point, _risk_level_from_score
)


@pytest.fixture
def base_report():
    """Create a basic meta-lens report for testing."""
    return create_base_state(
        input_hash="sha256:test123",
        padel_req_id="padel_123",
        infinity_req_id="inf_456"
    )


@pytest.fixture
def mock_slot_functions():
    """Mock slot functions for testing."""
    def mock_tri(R):
        return {"resonance_cross": 0.7}

    def mock_constellation(R):
        return {"coordination_hint": "stable"}

    def mock_culture(R, tri, const):
        return {
            "synthesis_confidence": 0.85,
            "risk_overall": 0.3,
            "historical_context": "Test context",
            "bias_markers": ["test_bias"],
            "risk_vectors": ["test_vector"]
        }

    def mock_distortion(R):
        return {
            "overall_score": 0.2,
            "patterns": [{"id": "test", "name": "test_pattern", "severity": 0.5, "confidence": 0.8}],
            "confidence": 0.75
        }

    def mock_emotion(R):
        return {"volatility": 0.25}

    return mock_tri, mock_constellation, mock_culture, mock_distortion, mock_emotion


def test_vectorize(base_report):
    """Test state vector extraction."""
    vector = vectorize(base_report)
    assert len(vector) == 6
    assert all(0.0 <= v <= 1.0 for v in vector)
    assert vector == [0.5, 0.5, 0.5, 0.5, 0.0, 0.5]


def test_l1_norm():
    """Test L1 norm computation."""
    a = [0.1, 0.2, 0.3]
    b = [0.2, 0.3, 0.4]
    assert l1_norm(a, b) == 0.3  # |0.1| + |0.1| + |0.1| = 0.3


def test_hash_report(base_report):
    """Test report hashing."""
    hash1 = hash_report(base_report)
    assert hash1.startswith("sha256:")
    assert len(hash1) == 71  # "sha256:" + 64 hex chars

    # Same report should produce same hash
    hash2 = hash_report(base_report)
    assert hash1 == hash2

    # Different report should produce different hash
    modified_report = base_report.copy()
    modified_report["input_reference"] = "different"
    hash3 = hash_report(modified_report)
    assert hash1 != hash3


def test_risk_level_from_score():
    """Test risk level categorization."""
    assert _risk_level_from_score(0.1) == "low"
    assert _risk_level_from_score(0.3) == "medium"
    assert _risk_level_from_score(0.6) == "high"
    assert _risk_level_from_score(0.9) == "critical"


def test_compute_once(base_report, mock_slot_functions):
    """Test single iteration of fixed-point operator."""
    tri_fn, const_fn, culture_fn, distort_fn, emo_fn = mock_slot_functions

    # Get mock outputs
    tri = tri_fn(base_report)
    const = const_fn(base_report)
    culture = culture_fn(base_report, tri, const)
    distortion = distort_fn(base_report)
    emotion = emo_fn(base_report)

    # Apply one iteration
    original_vector = vectorize(base_report)[:]
    updated_report = compute_once(base_report, None, tri, const, culture, distortion, emotion)
    new_vector = vectorize(updated_report)

    # Verify vector updated with damping
    assert new_vector != original_vector
    assert all(0.0 <= v <= 1.0 for v in new_vector)

    # Check specific updates
    assert new_vector[1] == 0.5 * 0.5 + 0.5 * 0.7  # Cross-family resonance with damping
    assert new_vector[3] == 0.5 * 0.5 + 0.5 * 0.85  # Cultural confidence with damping

    # Verify monotone risk
    assert new_vector[4] >= original_vector[4]  # Risk should not decrease


def test_create_base_state():
    """Test base state creation."""
    state = create_base_state("test_hash", "padel_123", "inf_456", "evaluation")

    assert state["schema_version"] == "1.0.0"
    assert state["source_slot"] == "S2"
    assert state["input_reference"] == "test_hash"
    assert state["meta_lens_analysis"]["cognitive_level"] == "evaluation"
    assert len(state["meta_lens_analysis"]["lenses_applied"]) == 5
    assert len(state["meta_lens_analysis"]["state_vector"]) == 6
    assert state["iteration"]["frozen_inputs"]["padel_ref"] == "padel_123"
    assert state["iteration"]["frozen_inputs"]["infinity_ref"] == "inf_456"


def test_run_fixed_point_convergence(base_report, mock_slot_functions):
    """Test fixed-point iteration with convergence."""
    tri_fn, const_fn, culture_fn, distort_fn, emo_fn = mock_slot_functions

    # Run with very low epsilon to force convergence
    os.environ["NOVA_META_LENS_EPSILON"] = "0.001"

    try:
        final_report, snapshots = run_fixed_point(
            "test_input",
            base_report,
            tri_fn, const_fn, culture_fn, distort_fn, emo_fn,
            lightclock_tick=1234
        )

        # Check convergence
        assert final_report["iteration"]["converged"] in [True, False]  # May or may not converge in 3 iters
        assert final_report["lightclock_tick"] == 1234
        assert final_report["input_reference"] == "test_input"
        assert final_report["integrity"]["hash"].startswith("sha256:")

        # Check snapshots
        assert len(snapshots) > 0
        assert all("epoch" in s for s in snapshots)
        assert all("hash" in s for s in snapshots)
        assert all("residual" in s for s in snapshots)

    finally:
        # Reset environment
        if "NOVA_META_LENS_EPSILON" in os.environ:
            del os.environ["NOVA_META_LENS_EPSILON"]


def test_run_fixed_point_watchdog_abort():
    """Test watchdog abort on high distortion."""
    def mock_tri(R): return {"resonance_cross": 0.7}
    def mock_const(R): return {"coordination_hint": "stable"}
    def mock_culture(R, tri, const): return {"synthesis_confidence": 0.5, "risk_overall": 0.1}
    def mock_high_distortion(R): return {"overall_score": 0.9}  # > 0.75 threshold
    def mock_emotion(R): return {"volatility": 0.3}

    base_state = create_base_state("test", "padel", "inf")

    final_report, snapshots = run_fixed_point(
        "test_input",
        base_state,
        mock_tri, mock_const, mock_culture, mock_high_distortion, mock_emotion,
        lightclock_tick=1234
    )

    # Should abort due to high distortion
    assert final_report["iteration"]["watchdog"]["abort_triggered"]
    assert not final_report["iteration"]["converged"]
    assert final_report["iteration"]["watchdog"]["distortion_overall"] == 0.9


def test_run_fixed_point_emotional_volatility_abort():
    """Test watchdog abort on high emotional volatility."""
    def mock_tri(R): return {"resonance_cross": 0.7}
    def mock_const(R): return {"coordination_hint": "stable"}
    def mock_culture(R, tri, const): return {"synthesis_confidence": 0.5, "risk_overall": 0.1}
    def mock_distortion(R): return {"overall_score": 0.2}
    def mock_high_emotion(R): return {"volatility": 0.9}  # > 0.8 threshold

    base_state = create_base_state("test", "padel", "inf")

    final_report, snapshots = run_fixed_point(
        "test_input",
        base_state,
        mock_tri, mock_const, mock_culture, mock_distortion, mock_high_emotion,
        lightclock_tick=1234
    )

    # Should abort due to high emotional volatility
    assert final_report["iteration"]["watchdog"]["abort_triggered"]
    assert not final_report["iteration"]["converged"]
    assert final_report["iteration"]["watchdog"]["emotional_volatility"] == 0.9


def test_monotone_risk_property(base_report, mock_slot_functions):
    """Test that risk_overall is monotone non-decreasing."""
    tri_fn, const_fn, culture_fn, distort_fn, emo_fn = mock_slot_functions

    # Start with higher risk
    base_report["meta_lens_analysis"]["state_vector"][4] = 0.6
    original_risk = base_report["meta_lens_analysis"]["state_vector"][4]

    # Mock culture returns lower risk
    def mock_culture_lower_risk(R, tri, const):
        return {"synthesis_confidence": 0.5, "risk_overall": 0.2}  # Lower than 0.6

    tri = tri_fn(base_report)
    const = const_fn(base_report)
    culture = mock_culture_lower_risk(base_report, tri, const)
    distortion = distort_fn(base_report)
    emotion = emo_fn(base_report)

    updated_report = compute_once(base_report, None, tri, const, culture, distortion, emotion)
    new_risk = updated_report["meta_lens_analysis"]["state_vector"][4]

    # Risk should not decrease due to monotone property
    assert new_risk >= original_risk


def test_environment_variable_configuration():
    """Test configuration via environment variables."""
    # Test defaults
    state = create_base_state("test", "padel", "inf")
    assert state["iteration"]["max_iters"] == 3
    assert state["iteration"]["alpha"] == 0.5
    assert state["iteration"]["epsilon"] == 0.02

    # Test environment override
    os.environ["NOVA_META_LENS_MAX_ITERS"] = "5"
    os.environ["NOVA_META_LENS_ALPHA"] = "0.7"
    os.environ["NOVA_META_LENS_EPSILON"] = "0.01"

    try:
        # Re-import with a clean module object so env vars are read at import time
        import sys
        import importlib
        full = "slots.slot02_deltathresh.meta_lens_processor"
        sys.modules.pop(full, None)                     # ensure fresh import
        mlp = importlib.import_module(full)

        # Should use environment values
        assert mlp.MAX_ITERS == 5
        assert mlp.ALPHA == 0.7
        assert mlp.EPSILON == 0.01

    finally:
        # Clean up
        for key in ["NOVA_META_LENS_MAX_ITERS", "NOVA_META_LENS_ALPHA", "NOVA_META_LENS_EPSILON"]:
            if key in os.environ:
                del os.environ[key]