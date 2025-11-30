import pytest
from nova.orchestrator.core import NovaOrchestrator
from frameworks.enums import AnchorValidationMode, DeploymentGuardrailResult


@pytest.mark.asyncio
@pytest.mark.parametrize("mode", [AnchorValidationMode.STRICT, AnchorValidationMode.ANNOTATE])
async def test_anchor_valid_passes(mode):
    orchestrator = NovaOrchestrator()
    orchestrator.slot1.available = True
    orchestrator.anchor_validation_mode = mode

    called = []

    def verify(anchor_id, value):
        called.append(True)
        return True

    orchestrator.slot1.verify = verify
    event = {"anchor_id": "a", "payload": {"content": "x"}}
    cont, new_event = await orchestrator._handle_anchor_verification(event)
    assert cont
    assert new_event == event
    assert called


@pytest.mark.asyncio
async def test_anchor_missing_skips_verification():
    orchestrator = NovaOrchestrator()
    orchestrator.slot1.available = True

    called = []

    def verify(anchor_id, value):
        called.append(True)
        return True

    orchestrator.slot1.verify = verify
    event = {"payload": {"content": "x"}}
    cont, new_event = await orchestrator._handle_anchor_verification(event)
    assert cont
    assert new_event == event
    assert not called


@pytest.mark.asyncio
async def test_anchor_invalid_strict_blocks_and_emits():
    orchestrator = NovaOrchestrator()
    orchestrator.slot1.available = True
    orchestrator.anchor_validation_mode = AnchorValidationMode.STRICT
    orchestrator.slot1.verify = lambda a, v: False

    captured = []

    async def handler(payload):
        captured.append(payload)

    orchestrator.bus.subscribe("anchor_verification_failed", handler)
    event = {"anchor_id": "a", "payload": {"content": "x"}}
    cont, new_event = await orchestrator._handle_anchor_verification(event)
    assert not cont
    assert new_event == {"result": DeploymentGuardrailResult.BLOCKED_PRINCIPLE_VIOLATION}
    assert captured == [{"anchor_id": "a"}]


@pytest.mark.asyncio
async def test_anchor_invalid_annotate_continues_and_emits():
    orchestrator = NovaOrchestrator()
    orchestrator.slot1.available = True
    orchestrator.anchor_validation_mode = AnchorValidationMode.ANNOTATE
    orchestrator.slot1.verify = lambda a, v: False

    captured = []

    async def handler(payload):
        captured.append(payload)

    orchestrator.bus.subscribe("anchor_verification_failed", handler)
    event = {"anchor_id": "a", "payload": {"content": "x"}}
    cont, new_event = await orchestrator._handle_anchor_verification(event)
    assert cont
    assert new_event["anchor_status"] == "FAILED"
    assert captured == [{"anchor_id": "a"}]
