import pytest

import nova.orchestrator.adapters.slot9_distortion_protection as slot9_adapter


@pytest.fixture
def adapter(monkeypatch):
    monkeypatch.setattr(slot9_adapter, "AVAILABLE", True)
    monkeypatch.setattr(slot9_adapter, "ENGINE", object())
    return slot9_adapter.Slot9DistortionProtectionAdapter()


@pytest.mark.asyncio
async def test_detect_success(monkeypatch, adapter):
    class StubResponse:
        def dict(self):
            return {"status": "ok", "score": 0.2}

    class StubEngine:
        async def detect_distortion(self, request):
            assert request.content == "content"
            assert request.context == {"ctx": True}
            return StubResponse()

    monkeypatch.setattr(slot9_adapter, "ENGINE", StubEngine())

    result = await adapter.detect("content", {"ctx": True})
    assert result == {"status": "ok", "score": 0.2}


@pytest.mark.asyncio
async def test_detect_with_dict_response(monkeypatch, adapter):
    class StubEngine:
        async def detect_distortion(self, request):
            return {"status": "dict"}

    monkeypatch.setattr(slot9_adapter, "ENGINE", StubEngine())

    result = await adapter.detect("content", None)
    assert result == {"status": "dict"}


@pytest.mark.asyncio
async def test_detect_handles_exception(monkeypatch, adapter):
    class StubEngine:
        async def detect_distortion(self, request):
            raise RuntimeError("boom")

    monkeypatch.setattr(slot9_adapter, "ENGINE", StubEngine())

    result = await adapter.detect("bad", {})
    assert result == {"status": "error"}


@pytest.mark.asyncio
async def test_detect_when_unavailable(monkeypatch, adapter):
    monkeypatch.setattr(slot9_adapter, "ENGINE", None)
    monkeypatch.setattr(adapter, "available", False)

    result = await adapter.detect("content", None)
    assert result == {"status": "unavailable"}
