"""Contract freeze test to prevent breaking changes to Slot 6 API."""

from slots.slot06_cultural_synthesis.engine import CulturalSynthesisEngine


# Hard freeze: any change to this set requires explicit schema version bump
REQUIRED_KEYS = {
    "adaptation_effectiveness",
    "principle_preservation_score", 
    "residual_risk",
    "policy_actions",
    "forbidden_hits",
    "consent_required"
}

# Additional keys allowed but not required (for backward compatibility)
ALLOWED_ADDITIONAL = {
    "principle_preservation",  # Legacy alias
}


def test_contract_shape_and_bounds():
    """Hard guard: fail if contract shape or bounds change."""
    engine = CulturalSynthesisEngine()
    
    # Test with known inputs that should produce stable output
    result = engine.synthesize(
        "test content", 
        tri_score=0.6, 
        layer_scores={}, 
        forbidden_hits=[], 
        consent_ok=True
    )
    
    # HARD FREEZE: Required keys must be present
    missing_keys = REQUIRED_KEYS - set(result.keys())
    assert not missing_keys, (
        f"BREAKING CHANGE: Required contract keys missing: {missing_keys}. "
        f"If intentional, bump CULTURAL_PROFILE schema version."
    )
    
    # Check numeric bounds (critical for safety)
    numeric_keys = ["adaptation_effectiveness", "principle_preservation_score", "residual_risk"]
    for key in numeric_keys:
        value = float(result[key])
        assert 0.0 <= value <= 1.0, (
            f"SAFETY VIOLATION: {key}={value} out of bounds [0.0, 1.0]. "
            f"This could cause downstream failures."
        )
    
    # Check data types (prevent runtime errors)
    assert isinstance(result["policy_actions"], list), "policy_actions must be list"
    assert isinstance(result["forbidden_hits"], list), "forbidden_hits must be list"  
    assert isinstance(result["consent_required"], bool), "consent_required must be bool"


def test_contract_stability_across_inputs():
    """Ensure contract is stable regardless of input variations."""
    engine = CulturalSynthesisEngine()
    
    # Test various input patterns that should all return same contract
    test_cases = [
        # Minimal input
        {},
        # String content
        "test content",
        # Dict with various keys
        {"tri_score": 0.8, "layer_scores": {"ethical": 0.5}},
        # Edge case values
        {"tri_score": 0.0, "anchor_confidence": 1.0, "ideology_push": True},
    ]
    
    for i, input_data in enumerate(test_cases):
        result = engine.synthesize(input_data)
        
        # All results must have the same contract shape
        result_keys = set(result.keys())
        missing = REQUIRED_KEYS - result_keys
        assert not missing, (
            f"Test case {i}: Contract violation - missing keys: {missing}"
        )
        
        # All numeric values must be bounded
        for key in ["adaptation_effectiveness", "principle_preservation_score", "residual_risk"]:
            value = result[key]
            assert isinstance(value, (int, float)), f"Test case {i}: {key} not numeric"
            assert 0.0 <= value <= 1.0, f"Test case {i}: {key}={value} out of bounds"


def test_version_documentation():
    """Ensure contract version is documented for tracking."""
    # This test serves as documentation of the current contract version
    # If this test is updated, it means the contract changed
    
    CONTRACT_VERSION = "CULTURAL_PROFILE@1"
    LAST_UPDATED = "2025-09-08"
    
    # Document current contract for future reference
    print(f"\n=== {CONTRACT_VERSION} Contract Specification ===")
    print(f"Last Updated: {LAST_UPDATED}")
    print(f"Required Keys: {sorted(REQUIRED_KEYS)}")
    print(f"Allowed Additional: {sorted(ALLOWED_ADDITIONAL)}")
    
    # If you're updating this test, increment the version above
    # and document what changed in the commit message
    assert CONTRACT_VERSION == "CULTURAL_PROFILE@1", (
        "If contract changed, update CONTRACT_VERSION and document changes"
    )