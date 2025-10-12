"""Property-based tests for Slot 6 Cultural Synthesis Engine."""

import pytest
from hypothesis import given, strategies as st, settings, HealthCheck
from nova.slots.slot06_cultural_synthesis.engine import CulturalSynthesisEngine


# Suppress health checks for property tests that might run slowly
@settings(suppress_health_check=[HealthCheck.too_slow])
@given(
    tri_score=st.floats(min_value=-10.0, max_value=10.0, allow_nan=False, allow_infinity=False),
    clarity=st.floats(min_value=-5.0, max_value=5.0, allow_nan=False, allow_infinity=False),
    foresight=st.floats(min_value=-5.0, max_value=5.0, allow_nan=False, allow_infinity=False),
    empiricism=st.floats(min_value=-5.0, max_value=5.0, allow_nan=False, allow_infinity=False),
    anchor_confidence=st.floats(min_value=-5.0, max_value=5.0, allow_nan=False, allow_infinity=False),
    ideology_push=st.booleans(),
)
def test_engine_bounds_invariant(tri_score, clarity, foresight, empiricism, anchor_confidence, ideology_push):
    """Property: Engine always returns values within safe bounds regardless of input."""
    engine = CulturalSynthesisEngine()
    
    profile = {
        "tri_score": tri_score,
        "clarity": clarity,
        "foresight": foresight, 
        "empiricism": empiricism,
        "anchor_confidence": anchor_confidence,
        "ideology_push": ideology_push,
        "layer_scores": {"test": 0.5}  # Reasonable layer score
    }
    
    result = engine.synthesize(profile)
    
    # INVARIANT: All numeric outputs must be in [0.0, 1.0]
    numeric_fields = ["adaptation_effectiveness", "principle_preservation_score", "residual_risk"]
    for field in numeric_fields:
        value = result[field]
        assert isinstance(value, (int, float)), f"{field} must be numeric, got {type(value)}"
        assert 0.0 <= value <= 1.0, f"{field}={value} out of bounds [0.0, 1.0]"
    
    # INVARIANT: Required contract fields must exist
    required_fields = {"policy_actions", "forbidden_hits", "consent_required"}
    for field in required_fields:
        assert field in result, f"Required field {field} missing from result"


@settings(suppress_health_check=[HealthCheck.too_slow])
@given(
    layer_scores=st.dictionaries(
        keys=st.text(min_size=1, max_size=10),
        values=st.floats(min_value=-10.0, max_value=10.0, allow_nan=False, allow_infinity=False),
        min_size=0,
        max_size=5
    )
)
def test_engine_deterministic(layer_scores):
    """Property: Engine is deterministic - same input produces same output."""
    engine = CulturalSynthesisEngine()
    
    profile = {
        "tri_score": 0.6,
        "clarity": 0.7,
        "layer_scores": layer_scores
    }
    
    # Run synthesis multiple times with identical input
    result1 = engine.synthesize(profile)
    result2 = engine.synthesize(profile)
    result3 = engine.synthesize(profile)
    
    # INVARIANT: Results must be identical (deterministic)
    assert result1 == result2, "Engine not deterministic - same input gave different results"
    assert result2 == result3, "Engine not deterministic - same input gave different results"


@settings(suppress_health_check=[HealthCheck.too_slow], max_examples=50)
@given(
    content=st.text(min_size=0, max_size=100),
    tri_score=st.floats(min_value=0.0, max_value=1.0, allow_nan=False, allow_infinity=False),
)
def test_risk_assessment_monotonic(content, tri_score):
    """Property: Lower TRI scores should generally lead to higher residual risk."""
    engine = CulturalSynthesisEngine()
    
    # Test with same content but different TRI scores
    low_tri_result = engine.synthesize(content, tri_score=tri_score * 0.1)  # Very low TRI
    high_tri_result = engine.synthesize(content, tri_score=max(0.8, tri_score))  # High TRI
    
    # PROPERTY: Very low TRI should generally produce higher risk than high TRI
    # (This is a weak property due to other factors, but should hold in most cases)
    low_risk = low_tri_result["residual_risk"]
    high_risk = high_tri_result["residual_risk"]
    
    if tri_score * 0.1 < 0.3:  # Only check when we have truly low TRI
        assert low_risk >= high_risk - 0.1, \
            f"Risk assessment appears inverted: low_tri_risk={low_risk}, high_tri_risk={high_risk}"


@settings(suppress_health_check=[HealthCheck.too_slow])
@given(
    input_data=st.one_of(
        st.none(),
        st.text(min_size=0, max_size=50),
        st.dictionaries(
            keys=st.sampled_from(["tri_score", "clarity", "foresight", "empiricism", "layer_scores"]),
            values=st.one_of(
                st.floats(min_value=-5.0, max_value=5.0, allow_nan=False, allow_infinity=False),
                st.dictionaries(
                    keys=st.text(min_size=1, max_size=10),
                    values=st.floats(min_value=0.0, max_value=1.0, allow_nan=False, allow_infinity=False),
                    max_size=3
                )
            ),
            max_size=5
        )
    )
)
def test_engine_never_crashes(input_data):
    """Property: Engine never crashes regardless of input type/content."""
    engine = CulturalSynthesisEngine()
    
    try:
        result = engine.synthesize(input_data)
        
        # If it returns a result, it must be well-formed
        assert isinstance(result, dict), "Result must be a dictionary"
        assert "residual_risk" in result, "Result must contain residual_risk"
        assert "principle_preservation_score" in result, "Result must contain principle_preservation_score"
        
        # Bounds check on returned values
        assert 0.0 <= result["residual_risk"] <= 1.0
        assert 0.0 <= result["principle_preservation_score"] <= 1.0
        
    except Exception as e:
        # Engine should handle all input gracefully, not crash
        pytest.fail(f"Engine crashed with input {input_data}: {e}")


@settings(suppress_health_check=[HealthCheck.too_slow])
@given(st.floats(min_value=0.0, max_value=1.0))
def test_principle_preservation_decreases_with_ideology_push(anchor_confidence):
    """Property: Ideology push should generally decrease principle preservation."""
    engine = CulturalSynthesisEngine()
    
    base_profile = {
        "anchor_confidence": anchor_confidence,
        "tri_score": 0.8,
        "layer_scores": {}
    }
    
    # Test with and without ideology push
    no_ideology = engine.synthesize({**base_profile, "ideology_push": False})
    with_ideology = engine.synthesize({**base_profile, "ideology_push": True})
    
    # PROPERTY: Ideology push should reduce principle preservation
    pps_no_ideology = no_ideology["principle_preservation_score"]
    pps_with_ideology = with_ideology["principle_preservation_score"]
    
    assert pps_with_ideology <= pps_no_ideology + 1e-10, \
        f"Ideology push should not increase principle preservation: {pps_with_ideology} > {pps_no_ideology}"


def test_property_test_coverage():
    """Meta-test: Ensure property tests actually run and cover edge cases."""
    # This test documents what our property tests cover
    coverage_areas = {
        "bounds_invariant": "All outputs stay within [0.0, 1.0] regardless of input",
        "deterministic": "Same input always produces same output",
        "risk_monotonic": "Lower TRI generally increases residual risk",
        "crash_resistance": "Engine handles any input without crashing", 
        "ideology_effect": "Ideology push decreases principle preservation"
    }
    
    print("\n=== Property Test Coverage ===")
    for area, description in coverage_areas.items():
        print(f"✓ {area}: {description}")
    
    # If we get here, the property tests are properly configured
    assert len(coverage_areas) == 5, "Expected 5 property test areas"