import logging
import nova.orchestrator.adapters.slot6_cultural as slot6
from frameworks.enums import DeploymentGuardrailResult


class BrokenEngine:
    def validate_cultural_deployment(self, profile, institution_type, payload):
        raise RuntimeError("boom")


def test_validate_logs_and_returns_error(monkeypatch, caplog):
    monkeypatch.setattr(slot6, "ENGINE", BrokenEngine())
    adapter = slot6.Slot6Adapter()
    profile = slot6.CulturalProfile()
    with caplog.at_level(logging.ERROR):
        result = adapter.validate(profile, "foo", {})
    assert result.result == DeploymentGuardrailResult.ERROR
    assert result.violations == ["boom"]
    assert any(
        "Cultural deployment validation failed" in record.message
        for record in caplog.records
    )
