import asyncio
import importlib
import sys
import types

import pytest


@pytest.fixture
def adapter_testbed(monkeypatch):
    """Load the slot1 orchestrator adapter with a controllable engine stub."""
    events = {}

    class DummyEngine:
        def __init__(self, **kwargs):
            events["init_kwargs"] = kwargs

        async def analyze_content(self, content, request_id, domain):
            events["last_analyze"] = (content, request_id, domain)
            result = events.get("analysis_result")
            if callable(result):
                return result(content, request_id, domain)
            if result is not None:
                return result
            return {
                "truth_score": 0.91,
                "anchor_stable": True,
                "anchor_used": domain,
                "timestamp": 123456.0,
                "version": "stub",
            }

        def establish_anchor(self, domain, facts):
            events["establish_args"] = (domain, tuple(facts))
            if events.get("establish_exception"):
                raise events["establish_exception"]
            return f"{domain}:{len(facts)}"

        def verify_anchor(self, domain):
            events["verify_args"] = domain
            if events.get("verify_exception"):
                raise events["verify_exception"]
            return {"exists": True, "verified": True, "domain": domain}

        def cleanup(self):
            events["cleanup_called"] = True
            if events.get("cleanup_exception"):
                raise events["cleanup_exception"]
            return events.get("cleanup_result", 2)

    fake_core = types.ModuleType("nova.slots.slot01_truth_anchor.core")
    fake_core.TruthAnchorEngine = DummyEngine
    monkeypatch.setitem(sys.modules, fake_core.__name__, fake_core)

    sys.modules.pop("nova.slots.slot01_truth_anchor.orchestrator_adapter", None)
    adapter_module = importlib.import_module("nova.slots.slot01_truth_anchor.orchestrator_adapter")
    adapter_module = importlib.reload(adapter_module)

    monkeypatch.setattr(adapter_module, "slot1_adapter", adapter_module.Slot1Adapter())

    def factory(**config):
        return adapter_module.Slot1Adapter(config if config else None)

    return adapter_module, events, factory


@pytest.mark.asyncio
async def test_run_success_returns_slotresult_ok(adapter_testbed):
    adapter, events, factory = adapter_testbed
    slot_adapter = factory(cache_max=256)

    payload = {"content": "evidence", "anchor_domain": "truth.domain"}
    result = await slot_adapter.run(payload, request_id="req-1")
    await asyncio.sleep(0)

    assert result.status == "ok"
    assert events["last_analyze"] == ("evidence", "req-1", "truth.domain")
    assert result.data["anchor_domain"] == "truth.domain"
    assert result.data["truth_score"] == pytest.approx(0.91)

    metrics = slot_adapter.get_metrics()
    assert metrics["total_requests"] >= 1
    assert metrics["failed_requests"] == 0


@pytest.mark.asyncio
async def test_run_rejects_invalid_payload_type(adapter_testbed):
    _, _, factory = adapter_testbed
    slot_adapter = factory()

    result = await slot_adapter.run("not-a-dict", request_id="req-2")
    await asyncio.sleep(0)

    assert result.status == "error"
    assert result.error.startswith("invalid_payload_type")


@pytest.mark.asyncio
async def test_run_requires_content_string(adapter_testbed):
    _, _, factory = adapter_testbed
    slot_adapter = factory()

    result = await slot_adapter.run({"anchor_domain": "domain"}, request_id="req-3")
    await asyncio.sleep(0)

    assert result.status == "error"
    assert result.error.startswith("invalid_content")


@pytest.mark.asyncio
async def test_run_wraps_engine_error(adapter_testbed):
    _, events, factory = adapter_testbed
    slot_adapter = factory()
    events["analysis_result"] = {"error": "engine down"}

    result = await slot_adapter.run({"content": "text"}, request_id="req-4")
    await asyncio.sleep(0)

    assert result.status == "error"
    assert result.error.startswith("engine_error")


@pytest.mark.asyncio
async def test_run_respects_shutdown_flag(adapter_testbed):
    _, _, factory = adapter_testbed
    slot_adapter = factory()
    slot_adapter._shutdown = True

    result = await slot_adapter.run({"content": "text"}, request_id="req-5")

    assert result.status == "error"
    assert result.error == "adapter_shutdown"


def test_establish_anchor_validation(adapter_testbed):
    _, events, factory = adapter_testbed
    slot_adapter = factory()

    with pytest.raises(ValueError):
        slot_adapter.establish_anchor("", ["fact"])

    with pytest.raises(ValueError):
        slot_adapter.establish_anchor("domain", [])

    established = slot_adapter.establish_anchor("domain", ["fact1", "fact2"])
    assert established == "domain:2"
    assert events["establish_args"] == ("domain", ("fact1", "fact2"))


def test_verify_anchor_handles_engine_exception(adapter_testbed):
    _, events, factory = adapter_testbed
    slot_adapter = factory()

    invalid = slot_adapter.verify_anchor("")
    assert invalid["exists"] is False
    assert invalid["verified"] is False

    events["verify_exception"] = RuntimeError("boom")
    verification = slot_adapter.verify_anchor("domain")
    assert verification["exists"] is False
    assert verification["verified"] is False
    assert verification["error"] == "boom"


def test_cleanup_cache_handles_variants(adapter_testbed):
    _, events, factory = adapter_testbed
    slot_adapter = factory()

    assert slot_adapter.cleanup_cache() == 2
    assert events["cleanup_called"] is True

    slot_adapter.engine = type("NoCleanup", (), {})()
    assert slot_adapter.cleanup_cache() == 0

    replacement = factory()
    events["cleanup_exception"] = RuntimeError("fail")
    slot_adapter.engine = replacement.engine
    assert slot_adapter.cleanup_cache() == 0


@pytest.mark.asyncio
async def test_metrics_capture_success_and_failure(adapter_testbed):
    _, _, factory = adapter_testbed
    slot_adapter = factory()

    await slot_adapter.run({"content": "alpha"}, request_id="success")
    await slot_adapter.run({}, request_id="failure")
    await asyncio.sleep(0)
    await asyncio.sleep(0)

    metrics = slot_adapter.get_metrics()
    assert metrics["total_requests"] >= 2
    assert metrics["failed_requests"] >= 1
    assert metrics["success_count"] == metrics["total_requests"] - metrics["failed_requests"]


@pytest.mark.asyncio
async def test_orchestrator_entrypoints_follow_lifecycle(adapter_testbed):
    adapter, events, _ = adapter_testbed

    new_adapter = await adapter.initialize({"cache_max": 999})
    assert events["init_kwargs"]["cache_max"] == 999
    assert new_adapter is adapter.slot1_adapter

    result = await adapter.run({"content": "payload"}, request_id="global-1")
    await asyncio.sleep(0)
    assert result.status == "ok"

    await adapter.shutdown()
    halted = await adapter.run({"content": "payload"}, request_id="global-2")
    assert halted.status == "error"
    assert halted.error == "adapter_shutdown"
