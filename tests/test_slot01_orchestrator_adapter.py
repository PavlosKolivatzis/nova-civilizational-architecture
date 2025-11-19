"""
Slot01 orchestrator adapter tests (dual-mode: legacy + root-mode).

Tests adapt based on NOVA_SLOT01_ROOT_MODE flag:
- When 0: Legacy adapter (analyze_content, truth_score, SlotResult)
- When 1: Root-Mode adapter (register/lookup/verify ops, dict response)
"""
import asyncio
import importlib
import os
import sys
import types

import pytest


def is_root_mode():
    """Check if Root-Mode is enabled for this test run."""
    return os.getenv("NOVA_SLOT01_ROOT_MODE", "0").strip() == "1"


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

    # Force adapter reinitialization to pick up flag
    adapter_module._slot1_adapter = None

    def factory(**config):
        if is_root_mode():
            return adapter_module.Slot1RootModeAdapter(config if config else None)
        else:
            from nova.slots.slot01_truth_anchor.legacy_adapter import Slot1LegacyAdapter
            return Slot1LegacyAdapter(config if config else None)

    return adapter_module, events, factory


# ============================================================================
# LEGACY MODE TESTS (NOVA_SLOT01_ROOT_MODE=0)
# ============================================================================

@pytest.mark.skipif(is_root_mode(), reason="Legacy tests only")
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


@pytest.mark.skipif(is_root_mode(), reason="Legacy tests only")
@pytest.mark.asyncio
async def test_run_rejects_invalid_payload_type(adapter_testbed):
    _, _, factory = adapter_testbed
    slot_adapter = factory()

    result = await slot_adapter.run("not-a-dict", request_id="req-2")
    await asyncio.sleep(0)

    assert result.status == "error"
    assert result.error.startswith("invalid_payload_type")


@pytest.mark.skipif(is_root_mode(), reason="Legacy tests only")
@pytest.mark.asyncio
async def test_run_requires_content_string(adapter_testbed):
    _, _, factory = adapter_testbed
    slot_adapter = factory()

    result = await slot_adapter.run({"anchor_domain": "domain"}, request_id="req-3")
    await asyncio.sleep(0)

    assert result.status == "error"
    assert result.error.startswith("invalid_content")


@pytest.mark.skipif(is_root_mode(), reason="Legacy tests only")
@pytest.mark.asyncio
async def test_run_wraps_engine_error(adapter_testbed):
    _, events, factory = adapter_testbed
    slot_adapter = factory()
    events["analysis_result"] = {"error": "engine down"}

    result = await slot_adapter.run({"content": "text"}, request_id="req-4")
    await asyncio.sleep(0)

    assert result.status == "error"
    assert result.error.startswith("engine_error")


@pytest.mark.skipif(is_root_mode(), reason="Legacy tests only")
@pytest.mark.asyncio
async def test_run_respects_shutdown_flag(adapter_testbed):
    _, _, factory = adapter_testbed
    slot_adapter = factory()
    slot_adapter._shutdown = True

    result = await slot_adapter.run({"content": "text"}, request_id="req-5")

    assert result.status == "error"
    assert result.error == "adapter_shutdown"


@pytest.mark.skipif(is_root_mode(), reason="Legacy tests only")
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


@pytest.mark.skipif(is_root_mode(), reason="Legacy tests only")
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


@pytest.mark.skipif(is_root_mode(), reason="Legacy tests only")
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


@pytest.mark.skipif(is_root_mode(), reason="Legacy tests only")
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


@pytest.mark.skipif(is_root_mode(), reason="Legacy tests only")
@pytest.mark.asyncio
async def test_orchestrator_entrypoints_follow_lifecycle(adapter_testbed):
    adapter, events, _ = adapter_testbed

    new_adapter = await adapter.initialize({"cache_max": 999})
    assert events["init_kwargs"]["cache_max"] == 999

    result = await adapter.run({"content": "payload"}, request_id="global-1")
    await asyncio.sleep(0)
    assert result.status == "ok"

    await adapter.shutdown()


# ============================================================================
# ROOT-MODE TESTS (NOVA_SLOT01_ROOT_MODE=1)
# ============================================================================

@pytest.mark.skipif(not is_root_mode(), reason="Root-Mode tests only")
@pytest.mark.asyncio
async def test_root_mode_register_anchor():
    """Root-Mode: register immutable anchor."""
    from nova.slots.slot01_truth_anchor.orchestrator_adapter import run

    result = await run({
        "op": "register",
        "anchor_id": "test.root.001",
        "value": "immutable_truth",
        "metadata": {"source": "pytest"}
    }, request_id="root-reg-001")

    assert result["success"] is True
    assert result["status"] == "ok"
    assert result["slot"] == "slot01"


@pytest.mark.skipif(not is_root_mode(), reason="Root-Mode tests only")
@pytest.mark.asyncio
async def test_root_mode_lookup_anchor():
    """Root-Mode: lookup registered anchor."""
    from nova.slots.slot01_truth_anchor.orchestrator_adapter import run

    # Register first
    await run({
        "op": "register",
        "anchor_id": "test.root.002",
        "value": "test_value",
        "metadata": {"test": True}
    }, request_id="root-reg-002")

    # Lookup
    result = await run({
        "op": "lookup",
        "anchor_id": "test.root.002"
    }, request_id="root-lookup-002")

    assert result["success"] is True
    assert result["found"] is True
    assert result["value"] == "test_value"
    assert result["metadata"]["test"] is True


@pytest.mark.skipif(not is_root_mode(), reason="Root-Mode tests only")
@pytest.mark.asyncio
async def test_root_mode_verify_anchor():
    """Root-Mode: verify claim against anchor."""
    from nova.slots.slot01_truth_anchor.orchestrator_adapter import run

    # Register
    await run({
        "op": "register",
        "anchor_id": "test.root.003",
        "value": "verify_me"
    }, request_id="root-reg-003")

    # Verify correct claim
    result = await run({
        "op": "verify",
        "anchor_id": "test.root.003",
        "claim": "verify_me"
    }, request_id="root-verify-003")

    assert result["success"] is True
    assert result["valid"] is True

    # Verify incorrect claim
    invalid = await run({
        "op": "verify",
        "anchor_id": "test.root.003",
        "claim": "wrong_value"
    }, request_id="root-verify-003b")

    assert invalid["success"] is True
    assert invalid["valid"] is False


@pytest.mark.skipif(not is_root_mode(), reason="Root-Mode tests only")
@pytest.mark.asyncio
async def test_root_mode_snapshot():
    """Root-Mode: get engine metrics snapshot."""
    from nova.slots.slot01_truth_anchor.orchestrator_adapter import run

    result = await run({
        "op": "snapshot"
    }, request_id="root-snapshot-001")

    assert result["success"] is True
    assert "snapshot" in result
    assert "anchors" in result["snapshot"]
    assert "lookups" in result["snapshot"]
    assert "failures" in result["snapshot"]


@pytest.mark.skipif(not is_root_mode(), reason="Root-Mode tests only")
@pytest.mark.asyncio
async def test_root_mode_export_secret_key():
    """Root-Mode: export secret key (hex)."""
    from nova.slots.slot01_truth_anchor.orchestrator_adapter import run

    result = await run({
        "op": "export_secret_key"
    }, request_id="root-export-001")

    assert result["success"] is True
    assert "key" in result
    assert isinstance(result["key"], str)
    assert len(result["key"]) > 0


@pytest.mark.skipif(not is_root_mode(), reason="Root-Mode tests only")
@pytest.mark.asyncio
async def test_root_mode_missing_operation():
    """Root-Mode: reject payload without 'op' field."""
    from nova.slots.slot01_truth_anchor.orchestrator_adapter import run

    result = await run({
        "anchor_id": "test"
    }, request_id="root-error-001")

    assert result["success"] is False
    assert result["error"] == "missing_operation"


@pytest.mark.skipif(not is_root_mode(), reason="Root-Mode tests only")
@pytest.mark.asyncio
async def test_root_mode_unknown_operation():
    """Root-Mode: reject unknown operation."""
    from nova.slots.slot01_truth_anchor.orchestrator_adapter import run

    result = await run({
        "op": "analyze_content",  # Old operation, not in Root-Mode
        "content": "test"
    }, request_id="root-error-002")

    assert result["success"] is False
    assert result["error"] == "unknown_operation"


@pytest.mark.skipif(not is_root_mode(), reason="Root-Mode tests only")
@pytest.mark.asyncio
async def test_root_mode_missing_parameters():
    """Root-Mode: reject incomplete payloads."""
    from nova.slots.slot01_truth_anchor.orchestrator_adapter import run

    # Register without value
    result = await run({
        "op": "register",
        "anchor_id": "test.incomplete"
    }, request_id="root-error-003")

    assert result["success"] is False
    assert result["error"] == "missing_parameters"

    # Verify without claim
    result = await run({
        "op": "verify",
        "anchor_id": "test.incomplete"
    }, request_id="root-error-004")

    assert result["success"] is False
    assert result["error"] == "missing_parameters"
