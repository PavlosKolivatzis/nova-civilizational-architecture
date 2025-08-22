import asyncio
import pytest

from slot06_cultural_synthesis.multicultural_truth_synthesis import (
    CulturalProfile,
    GuardrailValidationResult,
    DeploymentGuardrailResult,
)

from orchestrator.core import NovaOrchestrator


class StubSlot6:
    available = True

    def analyze(self, name, ctx):
        return CulturalProfile()

    def validate(self, profile, institution_type, payload):
        return GuardrailValidationResult(result=DeploymentGuardrailResult.APPROVED, compliance_score=1.0)


class StubTRI:
    available = False

    async def calibrate(self, payload):  # pragma: no cover - no-op
        return None


@pytest.mark.asyncio
async def test_orchestrator_routes_and_status() -> None:
    orch = NovaOrchestrator(slot6=StubSlot6(), slot4=StubTRI())
    approved: list = []

    async def on_approved(payload):
        approved.append(payload)

    orch.bus.subscribe("content.approved", on_approved)
    await orch.bus.publish(
        "content.validate",
        {"institution_name": "X", "institution_type": "t", "payload": {"content": "a"}},
    )
    assert approved and approved[0]["validation"].result == DeploymentGuardrailResult.APPROVED

    status = await orch.bus.publish("system.status", {})
    assert status[0]["slots"]["slot6_cultural"] is True
    assert "uptime" in status[0]
