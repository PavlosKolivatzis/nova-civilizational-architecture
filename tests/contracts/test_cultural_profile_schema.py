"""Contract tests for CULTURAL_PROFILE@1 schema stability."""



def test_cultural_profile_schema_v1():
    """Test CULTURAL_PROFILE@1 contract - freeze schema and validate bounds."""
    from nova.slots.slot06_cultural_synthesis.engine import CulturalSynthesisEngine
    
    engine = CulturalSynthesisEngine()
    
    # Test data that should produce valid synthesis
    test_profile = {
        "institution": "TestInstitution",
        "region": "EU",
        "clarity": 0.8,
        "foresight": 0.7,
        "empiricism": 0.9,
        "anchor_confidence": 0.85,
        "tri_score": 0.6,
        "layer_scores": {"ethical": 0.8, "factual": 0.9},
        "ideology_push": False
    }
    
    # Call synthesis
    result = engine.synthesize(test_profile)
    
    # Validate result is dict-like
    assert isinstance(result, dict), f"Expected dict, got {type(result)}"
    
    # Test required keys exist (CULTURAL_PROFILE@1 contract)
    required_keys = {
        "principle_preservation_score",
        "residual_risk",
        "policy_actions",
        "forbidden_hits", 
        "consent_required"
    }
    
    result_keys = set(result.keys())
    missing_keys = required_keys - result_keys
    assert not missing_keys, f"Missing required keys: {missing_keys}"
    
    # Test score bounds (critical for safety)
    assert 0.0 <= result["principle_preservation_score"] <= 1.0, \
        f"principle_preservation_score out of bounds: {result['principle_preservation_score']}"
    
    assert 0.0 <= result["residual_risk"] <= 1.0, \
        f"residual_risk out of bounds: {result['residual_risk']}"
    
    # Test data types
    assert isinstance(result["principle_preservation_score"], (int, float))
    assert isinstance(result["residual_risk"], (int, float))
    assert isinstance(result["policy_actions"], list)
    assert isinstance(result["forbidden_hits"], list)
    assert isinstance(result["consent_required"], bool)


def test_cultural_synthesis_safety_bounds():
    """Test that synthesis always produces safe bounds regardless of input."""
    from nova.slots.slot06_cultural_synthesis.engine import CulturalSynthesisEngine
    
    engine = CulturalSynthesisEngine()
    
    # Test edge cases
    test_cases = [
        # Empty profile
        {},
        # Extreme values
        {
            "clarity": 1.0,
            "foresight": 1.0, 
            "empiricism": 1.0,
            "anchor_confidence": 1.0,
            "tri_score": 1.0,
            "layer_scores": {"test": 1.0},
            "ideology_push": False
        },
        # Zero values  
        {
            "clarity": 0.0,
            "foresight": 0.0,
            "empiricism": 0.0, 
            "anchor_confidence": 0.0,
            "tri_score": 0.0,
            "layer_scores": {"test": 0.0},
            "ideology_push": True
        }
    ]
    
    for i, profile in enumerate(test_cases):
        result = engine.synthesize(profile)
        
        # All results must be safe
        assert 0.0 <= result["principle_preservation_score"] <= 1.0, \
            f"Test case {i}: PPS out of bounds"
        assert 0.0 <= result["residual_risk"] <= 1.0, \
            f"Test case {i}: residual_risk out of bounds"
        
        # High-risk content should have high residual risk
        if profile.get("tri_score", 0.5) < 0.3:  # Low TRI score = high risk
            assert result["residual_risk"] >= 0.5, \
                f"Test case {i}: Expected high residual risk for low TRI score"


def test_adapter_profile_validation():
    """Test adapter validates profiles correctly."""
    from nova.slots.slot06_cultural_synthesis.engine import CulturalSynthesisEngine
    from nova.slots.slot06_cultural_synthesis.adapter import CulturalSynthesisAdapter
    
    engine = CulturalSynthesisEngine()
    adapter = CulturalSynthesisAdapter(engine)
    
    # Test adapter returns proper profile
    profile = adapter.analyze_cultural_context("TestInst", {"region": "US"})
    
    # Should be dict-like with institution
    assert isinstance(profile, dict)
    assert "institution" in profile
    assert profile["institution"] == "TestInst"


def test_schema_version_stability():
    """Test that we can detect breaking changes to the schema."""
    from nova.slots.slot06_cultural_synthesis.engine import CulturalSynthesisEngine
    
    engine = CulturalSynthesisEngine()
    result = engine.synthesize({"tri_score": 0.5, "layer_scores": {}})
    
    # This test will fail if someone removes/renames core keys
    # Forcing explicit schema migration discussion
    expected_core_keys = {
        "principle_preservation_score", 
        "residual_risk",
        "policy_actions",
        "forbidden_hits",
        "consent_required"
    }
    
    actual_keys = set(result.keys())
    
    # Fail if core keys are missing (breaking change)
    missing_core = expected_core_keys - actual_keys
    assert not missing_core, \
        f"BREAKING CHANGE: Core schema keys missing: {missing_core}. " \
        f"If this is intentional, update CULTURAL_PROFILE schema version."
    
    # Document current schema for future comparison
    print(f"CULTURAL_PROFILE@1 keys: {sorted(actual_keys)}")


def test_risk_threshold_contract():
    """Test that risk assessment follows expected thresholds."""
    from nova.slots.slot06_cultural_synthesis.engine import CulturalSynthesisEngine
    
    engine = CulturalSynthesisEngine()
    
    # High quality input should produce low risk
    high_quality = {
        "tri_score": 0.9,
        "layer_scores": {"ethical": 0.9, "factual": 0.95},
        "anchor_confidence": 0.9,
        "clarity": 0.85,
        "foresight": 0.8,
        "empiricism": 0.9
    }
    
    result = engine.synthesize(high_quality)
    
    # Should produce low risk for high quality
    assert result["residual_risk"] < 0.7, \
        f"High quality input should produce low risk, got {result['residual_risk']}"
    
    assert result["principle_preservation_score"] > 0.3, \
        f"High quality input should preserve principles, got {result['principle_preservation_score']}"