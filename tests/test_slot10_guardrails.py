import pytest

from slot06_cultural_synthesis.multicultural_truth_synthesis import (
    CulturalProfile,
    GuardrailValidationResult,
    DeploymentGuardrailResult,
)
from slots.slot10_civilizational_deployment.mls import MetaLegitimacySeal
from slots.slot10_civilizational_deployment.models import MLSDecision


class StubSlot6:
    def __init__(self, result: DeploymentGuardrailResult):
        self.result = result

    def validate(self, profile, institution_type, payload):
        return GuardrailValidationResult(result=self.result, compliance_score=1.0)


def run(result: DeploymentGuardrailResult) -> MLSDecision:
    seal = MetaLegitimacySeal(StubSlot6(result))
    decision, _ = seal.assess(CulturalProfile(), "type", {})
    return decision


def test_mls_decisions() -> None:
    assert run(DeploymentGuardrailResult.APPROVED) == MLSDecision.ALLOW
    assert run(DeploymentGuardrailResult.REQUIRES_TRANSFORMATION) == MLSDecision.ALLOW_TRANSFORMED
    assert run(DeploymentGuardrailResult.BLOCKED_PRINCIPLE_VIOLATION) == MLSDecision.QUARANTINE
