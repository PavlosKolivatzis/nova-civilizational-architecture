"""Safety net tests to prevent critical regressions in Slot 6."""

import pytest
from slots.slot06_cultural_synthesis.adapter import CulturalSynthesisAdapter, DeploymentGuardrailResult
from frameworks.enums import DeploymentGuardrailResult as DGR


class HighRiskEngine:
    """Mock engine that always returns high-risk metrics."""
    
    def synthesize(self, *args, **kwargs):
        return {
            "principle_preservation_score": 0.2,  # Very low
            "residual_risk": 0.9,  # Very high
            "policy_actions": ["rephrase:high-risk"],
            "forbidden_hits": ["violence", "misinformation"],
            "consent_required": False,
            "adaptation_effectiveness": 0.1
        }


class AlwaysApproveEngine:
    """Mock engine that tries to always approve (security risk)."""
    
    def synthesize(self, *args, **kwargs):
        return {
            "principle_preservation_score": 1.0,  # Perfect score
            "residual_risk": 0.0,  # No risk (suspicious)
            "policy_actions": [],
            "forbidden_hits": [],
            "consent_required": False,
            "adaptation_effectiveness": 1.0
        }


def test_high_risk_never_approved():
    """Ensure high-risk content never gets approved."""
    adapter = CulturalSynthesisAdapter(engine=HighRiskEngine())
    
    # Test with high-risk slot2 result
    slot2_result = {
        "tri_score": 0.1,  # Very low TRI
        "layer_scores": {"violence": 0.95, "misinformation": 0.85},
        "forbidden_hits": ["violence", "misinformation"],
        "tri_gap": 0.7
    }
    
    result = adapter.validate_cultural_deployment(
        profile={"consent_ok": True},
        institution_type="educational",
        payload={"content": "High risk content"},
        slot2_result=slot2_result
    )
    
    # Must be blocked or require transformation, never approved
    assert result.result in (
        DGR.REQUIRES_TRANSFORMATION,
        DGR.BLOCKED_PRINCIPLE_VIOLATION,
        DGR.BLOCKED_CULTURAL_SENSITIVITY
    ), f"High-risk content was approved: {result.result}"
    
    # Should have violations
    assert len(result.violations) > 0, "High-risk content should have violations"
    
    # Compliance score should be low
    assert result.compliance_score < 0.7, f"Compliance score too high: {result.compliance_score}"


def test_forbidden_content_blocked():
    """Ensure content with forbidden hits gets blocked or transformed."""
    adapter = CulturalSynthesisAdapter(engine=HighRiskEngine())
    
    slot2_result = {
        "tri_score": 0.5,
        "layer_scores": {"ethical": 0.8},
        "forbidden_hits": ["forbidden_pattern", "sensitive_content"],
        "tri_gap": 0.3
    }
    
    result = adapter.validate_cultural_deployment(
        profile={"consent_ok": True},
        institution_type="public",
        payload={"content": "Content with forbidden patterns"},
        slot2_result=slot2_result
    )
    
    # Content with forbidden hits should never be approved
    assert result.result != DGR.APPROVED, "Forbidden content was approved"
    assert "forbidden_content" in result.violations or len(result.violations) > 0


def test_consent_required_blocks():
    """Ensure consent requirements are enforced."""
    adapter = CulturalSynthesisAdapter(engine=AlwaysApproveEngine())
    
    # Test with consent_required but no consent
    result = adapter.validate_cultural_deployment(
        profile={"consent_ok": False},  # No consent
        institution_type="healthcare", 
        payload={"content": "Sensitive medical content"},
        slot2_result={"tri_score": 0.8, "layer_scores": {}, "forbidden_hits": []}
    )
    
    # Must be blocked due to consent requirement
    assert result.result == DGR.BLOCKED_CULTURAL_SENSITIVITY, \
        "Content requiring consent was not blocked"
    assert "consent" in str(result.violations).lower()


def test_multiple_risk_factors_compound():
    """Test that multiple risk factors properly compound to prevent approval."""
    adapter = CulturalSynthesisAdapter(engine=HighRiskEngine())
    
    # Multiple risk factors
    slot2_result = {
        "tri_score": 0.15,  # Very low
        "layer_scores": {"ethical": 0.9, "factual": 0.8},  # High risk
        "forbidden_hits": ["sensitive"],
        "tri_gap": 0.65
    }
    
    result = adapter.validate_cultural_deployment(
        profile={"consent_ok": False},  # Also no consent
        institution_type="educational",
        payload={"content": "Multiple risk factors"},
        slot2_result=slot2_result
    )
    
    # With multiple risk factors, should definitely not be approved
    assert result.result != DGR.APPROVED, "High multi-risk content was approved"
    assert len(result.violations) >= 1, "Should have at least one violation"


def test_adapter_respects_engine_bounds():
    """Ensure adapter properly handles engine output bounds."""
    
    class OutOfBoundsEngine:
        """Mock engine with out-of-bounds values."""
        def synthesize(self, *args, **kwargs):
            return {
                "principle_preservation_score": 1.5,  # Out of bounds
                "residual_risk": -0.1,  # Out of bounds  
                "policy_actions": [],
                "forbidden_hits": [],
                "consent_required": False,
                "adaptation_effectiveness": 0.5
            }
    
    adapter = CulturalSynthesisAdapter(engine=OutOfBoundsEngine())
    
    # Even with out-of-bounds values, adapter should handle gracefully
    result = adapter.validate_cultural_deployment(
        profile={"consent_ok": True},
        institution_type="testing",
        payload={"content": "test"},
        slot2_result={"tri_score": 0.8, "layer_scores": {}, "forbidden_hits": []}
    )
    
    # Should not crash and should make a reasonable decision
    assert result.result in [DGR.APPROVED, DGR.REQUIRES_TRANSFORMATION, DGR.BLOCKED_PRINCIPLE_VIOLATION]
    assert 0.0 <= result.compliance_score <= 1.0, "Compliance score out of bounds"


@pytest.mark.parametrize("risk_level,expected_not_approved", [
    ({"pps": 0.1, "risk": 0.95}, True),   # Very high risk
    ({"pps": 0.25, "risk": 0.85}, True),  # High risk  
    ({"pps": 0.45, "risk": 0.65}, True),  # Medium-high risk
    ({"pps": 0.8, "risk": 0.2}, False),   # Low risk (can be approved)
])
def test_risk_thresholds_enforced(risk_level, expected_not_approved):
    """Test that risk thresholds are properly enforced."""
    
    class ConfigurableEngine:
        def __init__(self, pps, risk):
            self.pps = pps
            self.risk = risk
            
        def synthesize(self, *args, **kwargs):
            return {
                "principle_preservation_score": self.pps,
                "residual_risk": self.risk,
                "policy_actions": [],
                "forbidden_hits": [],
                "consent_required": False,
                "adaptation_effectiveness": 0.5
            }
    
    engine = ConfigurableEngine(risk_level["pps"], risk_level["risk"])
    adapter = CulturalSynthesisAdapter(engine=engine)
    
    result = adapter.validate_cultural_deployment(
        profile={"consent_ok": True},
        institution_type="testing",
        payload={"content": "test content"},
        slot2_result={"tri_score": 0.8, "layer_scores": {}, "forbidden_hits": []}
    )
    
    if expected_not_approved:
        assert result.result != DGR.APPROVED, \
            f"High-risk content (pps={risk_level['pps']}, risk={risk_level['risk']}) was approved"
    # Note: We don't assert approval for low-risk since other factors may still block