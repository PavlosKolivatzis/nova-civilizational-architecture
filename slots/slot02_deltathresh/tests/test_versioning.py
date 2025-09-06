from slots.slot02_deltathresh.adapters import adapt_processing_result
from slots.slot06_cultural_synthesis.engine import (
    slot2_threat_bridge,
    GuardrailValidationResult,
    DeploymentGuardrailResult,
)
from slots.slot10_civilizational_deployment.mls import MetaLegitimacySeal


def _legacy_payload():
    return {
        "content": "x",
        "action": "allow",
        "reason_codes": [],
        "tri_score": 0.9,
        "layer_scores": {"delta": 0.1},
        "processing_time_ms": 1.0,
        "content_hash": "abc",
        "neutralized_content": None,
        "quarantine_reason": None,
        "timestamp": 0.0,
        "operational_mode": None,
        "session_id": "default",
        "anchor_integrity": 1.0,
    }


class _StubSlot2:
    def __init__(self, payload):
        self.payload = payload
        self.config = type("C", (), {"tri_min_score": 0.8})

    def process_content(self, content, session_id):
        return self.payload


class _StubSlot6:
    def validate(self, profile, institution_type, payload):
        return GuardrailValidationResult(result=DeploymentGuardrailResult.APPROVED, compliance_score=1.0)


def test_adapt_and_consume_legacy_payload():
    payload = _legacy_payload()
    result = adapt_processing_result(payload)
    assert result.version == "v1"
    # Slot 6 consumer
    assert 0.0 <= slot2_threat_bridge(result, 0.8) <= 1.0
    # Slot 10 consumer with legacy dict
    mls = MetaLegitimacySeal(_StubSlot6(), slot2=_StubSlot2(payload))
    screen = mls._screen_with_slot2({"foo": "bar"})
    assert "threat_level" in screen
