"""Property-based safety tests for feature vector extraction.

Tests that build_feature_vector is total, bounded, and always 11-dimensional
across adversarial inputs using Hypothesis property-based testing.
"""

import math
import pytest
from hypothesis import given, strategies as st, settings
from orchestrator.router.features import build_feature_vector

# Keep runtime predictable on CI
settings.register_profile("ci", max_examples=150, deadline=500)
settings.load_profile("ci")


@st.composite
def adversarial_contexts(draw):
    """Generate adversarial context dictionaries with wide ranges and wrong types."""
    def adversarial_value(lo, hi):
        return draw(st.one_of(
            st.none(),                                          # Null values
            st.floats(min_value=lo, max_value=hi),              # Bounded floats
            st.floats(allow_nan=True, allow_infinity=True),     # NaN/Inf floats (no bounds)
            st.text(max_size=50),                              # Wrong type: string
            st.integers(min_value=-10**6, max_value=10**6),    # Wrong type: int
            st.lists(st.floats(), max_size=3),                 # Wrong type: list
            st.dictionaries(st.text(), st.floats(), max_size=2), # Wrong type: dict
        ))

    return {
        "tri_drift_z": adversarial_value(-10, 10),
        "system_pressure": adversarial_value(-5, 5),
        "cultural_residual_risk": adversarial_value(-5, 5),
        "backpressure_level": adversarial_value(-5, 5),
        "phase_jitter": adversarial_value(-5, 5),
        "dynamic_half_life_norm": adversarial_value(-5, 5),
        "transform_rate_hint": adversarial_value(-5, 5),
        "rollback_hint": adversarial_value(-5, 5),
        "latency_budget_norm": adversarial_value(-5, 5),
        "error_budget_remaining_norm": adversarial_value(-5, 5),
        # Add some unexpected keys
        "unexpected_key": adversarial_value(-1, 1),
        "another_unexpected": draw(st.text()),
    }


class TestFeatureVectorProperties:
    """Property-based tests for feature vector safety and correctness."""

    @given(adversarial_contexts())
    def test_build_feature_vector_total_function(self, ctx):
        """Test that build_feature_vector is a total function (never crashes)."""
        vec = build_feature_vector(ctx)

        # Verify basic properties
        assert isinstance(vec, list)
        assert len(vec) == 11

        for i, v in enumerate(vec):
            assert isinstance(v, (int, float)), f"Feature {i} not numeric: {type(v)}"
            assert math.isfinite(v), f"Feature {i} not finite: {v}"

        # Assert exact dimension and bounds in one place
        assert len(vec) == 11
        assert 0.0 <= vec[0] <= 1.0, f"tri_drift_z feature out of bounds: {vec[0]}"  # drift normalized by /3.0
        assert all(0.0 <= v <= 1.0 for v in vec[1:10]), f"Features out of bounds: {vec[1:10]}"
        assert vec[10] == pytest.approx(1.0), f"Bias term should be 1.0, got {vec[10]}"

    def test_build_feature_vector_with_valid_inputs(self):
        """Test feature vector properties with known valid inputs."""
        valid_contexts = [
            {},  # Empty context
            {"tri_drift_z": 0.5},  # Partial context
            {  # Complete normal context
                "tri_drift_z": 1.0,
                "system_pressure": 0.5,
                "cultural_residual_risk": 0.3,
                "backpressure_level": 0.4,
                "phase_jitter": 0.2,
                "dynamic_half_life_norm": 0.7,
                "transform_rate_hint": 0.1,
                "rollback_hint": 0.05,
                "latency_budget_norm": 0.8,
                "error_budget_remaining_norm": 0.9
            },
            {  # Extreme but valid values
                "tri_drift_z": 2.9,
                "system_pressure": 0.99,
                "cultural_residual_risk": 0.95,
                "backpressure_level": 0.98,
                "phase_jitter": 0.9,
                "dynamic_half_life_norm": 0.1,
                "transform_rate_hint": 0.95,
                "rollback_hint": 0.9,
                "latency_budget_norm": 0.1,
                "error_budget_remaining_norm": 0.05
            }
        ]

        for ctx in valid_contexts:
            vec = build_feature_vector(ctx)

            # Basic properties
            assert isinstance(vec, list)
            assert len(vec) == 11

            # All features should be numeric and finite
            for i, v in enumerate(vec):
                assert isinstance(v, (int, float)), f"Feature {i} not numeric: {type(v)}"
                assert math.isfinite(v), f"Feature {i} not finite: {v}"

            # Expected bounds based on current implementation
            # tri_drift_z is normalized by /3.0, so max should be around 1.0 for input <= 3.0
            assert 0.0 <= vec[0] <= 1.0, f"tri_drift_z feature out of bounds: {vec[0]}"

            # Other features should be in [0, 1] range
            for i in range(1, 10):
                assert 0.0 <= vec[i] <= 1.0, f"Feature {i} out of bounds: {vec[i]}"

            # Bias term should be 1.0
            assert vec[10] == pytest.approx(1.0), f"Bias term should be 1.0, got {vec[10]}"

    @given(st.dictionaries(
        st.sampled_from([
            "tri_drift_z", "system_pressure", "cultural_residual_risk",
            "backpressure_level", "phase_jitter", "dynamic_half_life_norm",
            "transform_rate_hint", "rollback_hint", "latency_budget_norm",
            "error_budget_remaining_norm"
        ]),
        st.floats(min_value=-1.0, max_value=3.0, allow_nan=False, allow_infinity=False),
        max_size=10
    ))
    def test_build_feature_vector_with_bounded_floats(self, ctx):
        """Test with bounded float inputs (should always work)."""
        vec = build_feature_vector(ctx)

        assert isinstance(vec, list)
        assert len(vec) == 11

        for i, v in enumerate(vec):
            assert isinstance(v, (int, float))
            assert math.isfinite(v)
            assert 0.0 <= v <= 1.0 or (i == 10 and v == 1.0)  # Allow bias term = 1.0

    def test_feature_vector_consistency(self):
        """Test that identical inputs produce identical outputs."""
        ctx = {
            "tri_drift_z": 0.5,
            "system_pressure": 0.3,
            "cultural_residual_risk": 0.2
        }

        vec1 = build_feature_vector(ctx)
        vec2 = build_feature_vector(ctx)

        assert vec1 == vec2, "Same input should produce same output"

    def test_feature_vector_defaults(self):
        """Test that missing keys use appropriate defaults."""
        empty_vec = build_feature_vector({})
        partial_vec = build_feature_vector({"tri_drift_z": 0.0})

        # Should have same length
        assert len(empty_vec) == len(partial_vec) == 11

        # tri_drift_z should be different
        assert empty_vec[0] == partial_vec[0]  # Both should be 0.0 normalized

        # Other features should be same (defaults)
        for i in range(1, 10):
            assert empty_vec[i] == partial_vec[i]

    def test_feature_vector_deterministic(self):
        """Test that feature extraction is deterministic."""
        ctx = {
            "tri_drift_z": 1.5,
            "system_pressure": 0.7,
            "cultural_residual_risk": 0.4,
            "backpressure_level": 0.6
        }

        # Multiple calls should produce identical results
        results = [build_feature_vector(ctx) for _ in range(10)]

        for i, vec in enumerate(results[1:], 1):
            assert vec == results[0], f"Run {i} produced different result"


class TestFeatureVectorBoundaries:
    """Test boundary conditions for feature vector extraction."""

    def test_zero_values(self):
        """Test with all zero values."""
        ctx = {key: 0.0 for key in [
            "tri_drift_z", "system_pressure", "cultural_residual_risk",
            "backpressure_level", "phase_jitter", "dynamic_half_life_norm",
            "transform_rate_hint", "rollback_hint", "latency_budget_norm",
            "error_budget_remaining_norm"
        ]}

        vec = build_feature_vector(ctx)

        # All features except bias should be 0.0
        for i in range(10):
            assert vec[i] == 0.0
        assert vec[10] == 1.0  # Bias term

    def test_maximum_values(self):
        """Test with maximum reasonable values."""
        ctx = {
            "tri_drift_z": 3.0,  # Maximum expected drift
            "system_pressure": 1.0,
            "cultural_residual_risk": 1.0,
            "backpressure_level": 1.0,
            "phase_jitter": 1.0,
            "dynamic_half_life_norm": 1.0,
            "transform_rate_hint": 1.0,
            "rollback_hint": 1.0,
            "latency_budget_norm": 1.0,
            "error_budget_remaining_norm": 1.0
        }

        vec = build_feature_vector(ctx)

        # All features should be <= 1.0
        for i in range(10):
            assert 0.0 <= vec[i] <= 1.0
        assert vec[10] == 1.0  # Bias term

    def test_negative_values(self):
        """Test with negative values (should be clamped to 0)."""
        ctx = {key: -1.0 for key in [
            "tri_drift_z", "system_pressure", "cultural_residual_risk",
            "backpressure_level", "phase_jitter", "dynamic_half_life_norm",
            "transform_rate_hint", "rollback_hint", "latency_budget_norm",
            "error_budget_remaining_norm"
        ]}

        vec = build_feature_vector(ctx)

        # All features should be clamped to >= 0.0
        for i in range(10):
            assert vec[i] >= 0.0
        assert vec[10] == 1.0  # Bias term

    @given(st.fixed_dictionaries({
        "tri_drift_z": st.floats(0, 3),
        "system_pressure": st.floats(0, 1),
        "cultural_residual_risk": st.floats(0, 1),
        "backpressure_level": st.floats(0, 1),
        "phase_jitter": st.floats(0, 0.5),
        "dynamic_half_life_norm": st.floats(0, 1),
        "transform_rate_hint": st.floats(0, 1),
        "rollback_hint": st.floats(0, 1),
        "latency_budget_norm": st.floats(0, 1),
        "error_budget_remaining_norm": st.floats(0, 1),
    }))
    def test_idempotent_when_already_valid(self, ctx):
        """Test that valid inputs are idempotent (shouldn't change)."""
        v1 = build_feature_vector(ctx)
        v2 = build_feature_vector(ctx)
        assert v1 == v2, "Same input should produce same output"

        # Should produce stable, bounded output
        assert len(v1) == 11
        assert 0.0 <= v1[0] <= 1.0  # tri_drift_z normalized
        assert all(0.0 <= v <= 1.0 for v in v1[1:10])
        assert v1[10] == pytest.approx(1.0)
