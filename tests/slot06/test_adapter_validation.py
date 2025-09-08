from types import SimpleNamespace

from slots.slot06_cultural_synthesis.adapter import (
    CulturalSynthesisAdapter,
    DeploymentGuardrailResult,
)


class DummyEngine:
    def synthesize(self, content, **k):
        return {
            "principle_preservation_score": k.get("pps", 0.9),
            "residual_risk": k.get("rr", 0.1),
            "policy_actions": [],
            "forbidden_hits": k.get("forbidden_hits", []),
            "consent_required": not k.get("consent_ok", True),
            "version": "x",
        }


def _adapter():
    ad = CulturalSynthesisAdapter(engine=DummyEngine())
    return ad


def test_blocks_when_consent_missing():
    ad = _adapter()
    s2 = {"tri_score": 0.6, "layer_scores": {}, "forbidden_hits": []}
    res = ad.validate_cultural_deployment(
        {"consent_ok": False},
        "inst",
        "text",
        s2,
    )
    assert res.result == DeploymentGuardrailResult.BLOCKED_CULTURAL_SENSITIVITY


def test_requires_transformation_on_elevated_risk():
    class Eng(DummyEngine):
        def synthesize(self, content, **k):
            d = super().synthesize(content, **k)
            d["residual_risk"] = 0.5  # ≥ RISK_TRANSFORM
            d["principle_preservation_score"] = 0.45
            return d

    ad = CulturalSynthesisAdapter(engine=Eng())
    s2 = {"tri_score": 0.5, "layer_scores": {}, "forbidden_hits": []}
    res = ad.validate_cultural_deployment({}, "inst", "text", s2)
    assert res.result == DeploymentGuardrailResult.REQUIRES_TRANSFORMATION


def test_blocks_on_forbidden_and_high_risk():
    class Eng(DummyEngine):
        def synthesize(self, content, **k):
            d = super().synthesize(content, **k)
            d["residual_risk"] = 0.9
            d["forbidden_hits"] = ["ruleX"]
            d["principle_preservation_score"] = 0.2
            return d

    ad = CulturalSynthesisAdapter(engine=Eng())
    s2 = {"tri_score": 0.4, "layer_scores": {}, "forbidden_hits": ["ruleX"]}
    res = ad.validate_cultural_deployment({}, "inst", "text", s2)
    assert res.result == DeploymentGuardrailResult.BLOCKED_PRINCIPLE_VIOLATION


def test_approves_when_low_risk_and_no_forbidden():
    ad = _adapter()
    s2 = {"tri_score": 0.7, "layer_scores": {}, "forbidden_hits": []}
    res = ad.validate_cultural_deployment({}, "inst", "text", s2)
    assert res.result == DeploymentGuardrailResult.APPROVED
