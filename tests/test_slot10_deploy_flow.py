import pytest

from slot06_cultural_synthesis.multicultural_truth_synthesis import (
    CulturalProfile,
    GuardrailValidationResult,
    DeploymentGuardrailResult,
)
from slots.slot10_civilizational_deployment import (
    InstitutionalNodeDeployer,
    MetaLegitimacySeal,
    NovaPhaseSpaceSimulator,
)


class StubSlot6:
    def __init__(self, result: DeploymentGuardrailResult = DeploymentGuardrailResult.APPROVED):
        self.result = result

    def analyze(self, institution_name, ctx):
        return CulturalProfile()

    def validate(self, profile, institution_type, payload):
        return GuardrailValidationResult(result=self.result, compliance_score=1.0)


class StubTRI:
    available = True

    async def calibrate(self, payload):  # pragma: no cover - simple stub
        return None


def make_deployer() -> InstitutionalNodeDeployer:
    slot6 = StubSlot6()
    tri = StubTRI()
    mls = MetaLegitimacySeal(slot6)
    phase = NovaPhaseSpaceSimulator()
    return InstitutionalNodeDeployer(slot6, tri, mls, phase)


@pytest.mark.asyncio
async def test_happy_path() -> None:
    dep = make_deployer()
    res = await dep.deploy("InstA", "academic", {"content": "x", "secure": True})
    assert res.approved is True
    assert dep.metrics.deployments == 1


@pytest.mark.asyncio
async def test_capacity_block() -> None:
    dep = make_deployer()
    res = await dep.deploy("InstA", "academic", {"content": "x", "capacity_block": True})
    assert res.approved is False
    assert res.reason == "capacity"
    assert dep.metrics.blocked == 1


@pytest.mark.asyncio
async def test_security_fail() -> None:
    dep = make_deployer()
    res = await dep.deploy("InstA", "academic", {"content": "x", "secure": False})
    assert res.approved is False
    assert res.reason == "security"
    assert dep.metrics.security_failures == 1
