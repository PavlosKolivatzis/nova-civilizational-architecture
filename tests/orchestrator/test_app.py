
import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def app_module(monkeypatch):
    import nova.orchestrator.app as app_mod

    async def startup_stub():
        return None

    async def shutdown_stub():
        return None

    async def sweeper_stub():
        return None

    async def canary_stub():
        return None

    monkeypatch.setattr(app_mod, "_startup", startup_stub)
    monkeypatch.setattr(app_mod, "_shutdown", shutdown_stub)
    monkeypatch.setattr(app_mod, "_sm_sweeper", lambda: sweeper_stub())
    monkeypatch.setattr(app_mod, "_canary_loop", lambda: canary_stub())

    return app_mod


@pytest.fixture
def client(app_module):
    with TestClient(app_module.app) as client:
        yield client


@pytest.mark.asyncio
async def test_handle_request_invokes_orchestrator(monkeypatch):
    import nova.orchestrator.app as app_mod

    monkeypatch.setattr(
        app_mod.router,
        "get_route",
        lambda target_slot, original_timeout=2.0: ("slot02_deltathresh", 3.5),
    )

    captured = {}

    async def fake_invoke(slot_fn, slot_name, payload, request_id, timeout=None):
        captured.update(
            {
                "slot_fn": slot_fn,
                "slot_name": slot_name,
                "payload": payload,
                "request_id": request_id,
                "timeout": timeout,
            }
        )
        return {"result": "ok"}

    fake_orch = type("FakeOrchestrator", (), {"invoke_slot": staticmethod(fake_invoke)})
    monkeypatch.setattr(app_mod, "orch", fake_orch)

    result = await app_mod.handle_request("slot02_deltathresh", {"payload": True}, "req-123")

    assert result.executed is True
    assert result.blocked is False
    assert result.reason == "executed"
    assert result.result == {"result": "ok"}
    assert result.slot_id == "slot02_deltathresh"
    assert result.timeout == 3.5
    assert captured["slot_name"] == "slot02_deltathresh"
    assert captured["payload"] == {"payload": True}
    assert captured["request_id"] == "req-123"
    assert captured["timeout"] == 3.5


@pytest.mark.asyncio
async def test_handle_request_no_orchestrator_returns_structured_result(monkeypatch):
    import nova.orchestrator.app as app_mod

    monkeypatch.setattr(
        app_mod.router,
        "get_route",
        lambda target_slot, original_timeout=2.0: ("slot02_deltathresh", 2.0),
    )
    monkeypatch.setattr(app_mod, "orch", None)
    result = await app_mod.handle_request("slot02_deltathresh", {"payload": False}, "req-999")
    assert result.executed is False
    assert result.blocked is False
    assert result.reason == "no_runner"
    assert result.result is None
    assert result.slot_id == "slot02_deltathresh"
    assert result.timeout == 2.0


def test_execution_mode_aliases_and_default(monkeypatch):
    import nova.orchestrator.app as app_mod

    monkeypatch.delenv("NOVA_EXECUTION_MODE", raising=False)
    assert app_mod._execution_mode() == "unified"

    monkeypatch.setenv("NOVA_EXECUTION_MODE", "legacy")
    assert app_mod._execution_mode() == "legacy"

    monkeypatch.setenv("NOVA_EXECUTION_MODE", "unified_shadow")
    assert app_mod._execution_mode() == "shadow"

    monkeypatch.setenv("NOVA_EXECUTION_MODE", "unified_live")
    assert app_mod._execution_mode() == "unified"


@pytest.mark.asyncio
async def test_handle_request_legacy_mode_dispatch(monkeypatch):
    import nova.orchestrator.app as app_mod

    monkeypatch.setenv("NOVA_EXECUTION_MODE", "legacy")
    calls = []

    async def fake_legacy(target_slot, payload, request_id):
        calls.append(("legacy", target_slot, dict(payload), request_id))
        return app_mod.ExecutionResult(
            executed=True,
            blocked=False,
            reason="executed",
            result={"ok": True},
            slot_id="slot02_deltathresh",
            timeout=2.0,
        )

    async def fake_unified(*args, **kwargs):
        raise AssertionError("unified path should not run in legacy mode")

    monkeypatch.setattr(app_mod, "_legacy_handle_request", fake_legacy)
    monkeypatch.setattr(app_mod, "_unified_handle_request", fake_unified)

    out = await app_mod.handle_request("slot02_deltathresh", {"x": 1}, "req-legacy")

    assert out.executed is True
    assert calls == [("legacy", "slot02_deltathresh", {"x": 1}, "req-legacy")]


@pytest.mark.asyncio
async def test_handle_request_shadow_mode_returns_legacy_and_compares(monkeypatch):
    import nova.orchestrator.app as app_mod

    monkeypatch.setenv("NOVA_EXECUTION_MODE", "shadow")
    calls = []
    compare_calls = []

    legacy_result = app_mod.ExecutionResult(
        executed=True,
        blocked=False,
        reason="executed",
        result={"path": "legacy"},
        slot_id="slot02_deltathresh",
        timeout=2.0,
    )
    unified_result = app_mod.ExecutionResult(
        executed=True,
        blocked=False,
        reason="executed",
        result={"path": "unified"},
        slot_id="slot02_deltathresh",
        timeout=2.0,
    )

    async def fake_legacy(target_slot, payload, request_id):
        calls.append(("legacy", target_slot, dict(payload), request_id))
        return legacy_result

    async def fake_unified(target_slot, payload, request_id):
        calls.append(("unified", target_slot, dict(payload), request_id))
        return unified_result

    def fake_compare(**kwargs):
        compare_calls.append(kwargs)

    monkeypatch.setattr(app_mod, "_legacy_handle_request", fake_legacy)
    monkeypatch.setattr(app_mod, "_unified_handle_request", fake_unified)
    monkeypatch.setattr(app_mod, "_log_shadow_execution_mismatch", fake_compare)

    out = await app_mod.handle_request("slot02_deltathresh", {"x": 9}, "req-shadow")

    assert out is legacy_result
    assert calls == [
        ("legacy", "slot02_deltathresh", {"x": 9}, "req-shadow"),
        ("unified", "slot02_deltathresh", {"x": 9}, "req-shadow"),
    ]
    assert len(compare_calls) == 1
    assert compare_calls[0]["legacy_result"] is legacy_result
    assert compare_calls[0]["unified_result"] is unified_result


@pytest.mark.asyncio
async def test_handle_request_mode_parity_success(monkeypatch):
    import nova.orchestrator.app as app_mod

    class FakeBus:
        async def publish(self, topic, event):
            return []

    class FakeRouter:
        def get_route(self, target_slot, original_timeout=2.0):
            return ("slot02_deltathresh", 3.5)

    async def fake_invoke(slot_fn, slot_name, payload, request_id, timeout=None):
        return {"slot": slot_name, "timeout": timeout, "request_id": request_id}

    fake_orch = type("FakeOrchestrator", (), {"invoke_slot": staticmethod(fake_invoke)})

    monkeypatch.setattr(app_mod, "bus", FakeBus())
    monkeypatch.setattr(app_mod, "router", FakeRouter())
    monkeypatch.setattr(app_mod, "orch", fake_orch)
    monkeypatch.setattr(app_mod, "SLOT_REGISTRY", {"slot02_deltathresh": object()})

    monkeypatch.setenv("NOVA_EXECUTION_MODE", "legacy")
    legacy = await app_mod.handle_request("slot02_deltathresh", {"x": 1}, "req-mode-1")

    monkeypatch.setenv("NOVA_EXECUTION_MODE", "unified")
    unified = await app_mod.handle_request("slot02_deltathresh", {"x": 1}, "req-mode-1")

    assert legacy == unified
    assert legacy.executed is True
    assert legacy.reason == "executed"


@pytest.mark.asyncio
async def test_handle_request_mode_parity_no_runner(monkeypatch):
    import nova.orchestrator.app as app_mod

    class FakeBus:
        async def publish(self, topic, event):
            return []

    class FakeRouter:
        def get_route(self, target_slot, original_timeout=2.0):
            return ("slot02_deltathresh", 2.0)

    monkeypatch.setattr(app_mod, "bus", FakeBus())
    monkeypatch.setattr(app_mod, "router", FakeRouter())
    monkeypatch.setattr(app_mod, "orch", None)
    monkeypatch.setattr(app_mod, "SLOT_REGISTRY", {"slot02_deltathresh": object()})

    monkeypatch.setenv("NOVA_EXECUTION_MODE", "legacy")
    legacy = await app_mod.handle_request("slot02_deltathresh", {"x": 0}, "req-mode-2")

    monkeypatch.setenv("NOVA_EXECUTION_MODE", "unified")
    unified = await app_mod.handle_request("slot02_deltathresh", {"x": 0}, "req-mode-2")

    assert legacy == unified
    assert legacy.executed is False
    assert legacy.blocked is False
    assert legacy.reason == "no_runner"


@pytest.mark.asyncio
async def test_handle_request_mode_parity_fallback_route(monkeypatch):
    import nova.orchestrator.app as app_mod

    class FakeBus:
        async def publish(self, topic, event):
            return []

    class FakeRouter:
        def get_route(self, target_slot, original_timeout=2.0):
            return ("slot08_memory_ethics", 4.0)

    async def fake_invoke(slot_fn, slot_name, payload, request_id, timeout=None):
        return {"slot": slot_name, "timeout": timeout, "request_id": request_id}

    fake_orch = type("FakeOrchestrator", (), {"invoke_slot": staticmethod(fake_invoke)})

    monkeypatch.setattr(app_mod, "bus", FakeBus())
    monkeypatch.setattr(app_mod, "router", FakeRouter())
    monkeypatch.setattr(app_mod, "orch", fake_orch)
    monkeypatch.setattr(
        app_mod,
        "SLOT_REGISTRY",
        {
            "slot02_deltathresh": object(),
            "slot08_memory_ethics": object(),
        },
    )

    monkeypatch.setenv("NOVA_EXECUTION_MODE", "legacy")
    legacy = await app_mod.handle_request("slot02_deltathresh", {"y": 2}, "req-mode-fb")

    monkeypatch.setenv("NOVA_EXECUTION_MODE", "unified")
    unified = await app_mod.handle_request("slot02_deltathresh", {"y": 2}, "req-mode-fb")

    assert legacy == unified
    assert legacy.executed is True
    assert legacy.slot_id == "slot08_memory_ethics"
    assert legacy.timeout == 4.0


def test_health_endpoint_returns_status_ok(app_module, client, monkeypatch):
    monkeypatch.setattr(
        app_module,
        "health_payload",
        lambda *args, **kwargs: {"slots": {"slot01_truth_anchor": {"status": "ok"}}},
    )

    response = client.get("/health")
    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ok"
    assert payload["slots"]["slot01_truth_anchor"] == {"status": "ok"}


def test_metrics_endpoint_respects_flag(app_module, monkeypatch):
    monkeypatch.delenv("NOVA_ENABLE_PROMETHEUS", raising=False)
    with TestClient(app_module.app) as client:
        resp = client.get("/metrics")
        assert resp.status_code == 404

    monkeypatch.setenv("NOVA_ENABLE_PROMETHEUS", "1")
    monkeypatch.setattr(
        "nova.orchestrator.prometheus_metrics.get_metrics_response",
        lambda: (b"metrics-data", "text/custom"),
    )
    with TestClient(app_module.app) as client:
        resp = client.get("/metrics")
        assert resp.status_code == 200
        assert resp.content == b"metrics-data"
        assert resp.headers["content-type"].startswith("text/custom")


def test_ops_self_check_reports_execution_mode(app_module, client, monkeypatch):
    import nova.orchestrator.app as app_mod

    monkeypatch.setenv("NOVA_EXECUTION_MODE", "unified_shadow")
    monkeypatch.setenv("NOVA_SHADOW_EXECUTION_MISMATCH_RATE_SLO", "0.2")
    monkeypatch.setattr(
        app_mod,
        "_shadow_execution_metrics",
        {"comparisons_total": 3, "matches_total": 2, "mismatches_total": 1, "reasons": {"result": 1}},
    )

    response = client.get("/ops/self-check")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["execution_mode"] == "shadow"
    assert body["execution_mode_raw"] == "unified_shadow"
    assert body["shadow_execution"] == {
        "comparisons_total": 3,
        "matches_total": 2,
        "mismatches_total": 1,
        "mismatch_rate": 1 / 3,
        "reasons": {"result": 1},
    }
    assert body["shadow_execution_slo"] == {
        "status": "out_of_threshold",
        "within_threshold": False,
        "threshold_mismatch_rate": 0.2,
        "observed_mismatch_rate": 1 / 3,
        "comparisons_total": 3,
        "mismatches_total": 1,
    }


def test_shadow_execution_metrics_record_match_and_mismatch(monkeypatch):
    import nova.orchestrator.app as app_mod

    monkeypatch.setattr(
        app_mod,
        "_shadow_execution_metrics",
        {"comparisons_total": 0, "matches_total": 0, "mismatches_total": 0, "reasons": {}},
    )

    same_a = app_mod.ExecutionResult(
        executed=True,
        blocked=False,
        reason="executed",
        result={"ok": True},
        slot_id="slot02_deltathresh",
        timeout=2.0,
    )
    same_b = app_mod.ExecutionResult(
        executed=True,
        blocked=False,
        reason="executed",
        result={"ok": True},
        slot_id="slot02_deltathresh",
        timeout=2.0,
    )
    diff = app_mod.ExecutionResult(
        executed=True,
        blocked=False,
        reason="executed",
        result={"ok": False},
        slot_id="slot02_deltathresh",
        timeout=2.0,
    )

    assert app_mod._record_shadow_execution_comparison(same_a, same_b) == []
    assert app_mod._record_shadow_execution_comparison(same_a, diff) == ["result"]
    assert app_mod._shadow_execution_metrics_snapshot() == {
        "comparisons_total": 2,
        "matches_total": 1,
        "mismatches_total": 1,
        "mismatch_rate": 0.5,
        "reasons": {"result": 1},
    }


def test_shadow_execution_slo_status_helper(monkeypatch):
    import nova.orchestrator.app as app_mod

    monkeypatch.setenv("NOVA_SHADOW_EXECUTION_MISMATCH_RATE_SLO", "0.25")
    no_data = app_mod._shadow_execution_slo_status(
        {"comparisons_total": 0, "mismatches_total": 0, "mismatch_rate": 0.0}
    )
    assert no_data["status"] == "no_data"
    assert no_data["within_threshold"] is None
    assert no_data["threshold_mismatch_rate"] == 0.25

    within = app_mod._shadow_execution_slo_status(
        {"comparisons_total": 10, "mismatches_total": 2, "mismatch_rate": 0.2}
    )
    assert within["status"] == "within_threshold"
    assert within["within_threshold"] is True

    outside = app_mod._shadow_execution_slo_status(
        {"comparisons_total": 10, "mismatches_total": 3, "mismatch_rate": 0.3}
    )
    assert outside["status"] == "out_of_threshold"
    assert outside["within_threshold"] is False


def test_force_expire_now_uses_semantic_mirror(app_module, monkeypatch):
    monkeypatch.setenv("NOVA_ALLOW_EXPIRE_TEST", "1")
    monkeypatch.setattr(
        "nova.orchestrator.prometheus_metrics.update_semantic_mirror_metrics", lambda: None
    )

    class DummyScope:
        PUBLIC = "PUBLIC"

    class StubMirror:
        def __init__(self):
            self._contexts = {}
            self._metrics = {
                "entries_expired": 0,
                "unlearn_pulses_sent": 0,
            }

        def get_context(self, *_, **__):
            return None

        def _cleanup_expired_entries(self, *_):
            self._metrics["entries_expired"] += 1
            self._metrics["unlearn_pulses_sent"] += 1
            self._contexts.clear()

    stub = StubMirror()
    monkeypatch.setattr("nova.orchestrator.semantic_mirror.ContextScope", DummyScope)
    monkeypatch.setattr("nova.orchestrator.semantic_mirror.get_semantic_mirror", lambda: stub)

    with TestClient(app_module.app) as client:
        resp = client.post("/ops/expire-now")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "ok"
        assert data["expired_count"] >= 1
        assert data["pulses_delta"] >= 1


def test_build_http_decision_context_helper(monkeypatch):
    import types
    import nova.orchestrator.app as app_mod

    monkeypatch.setenv("NOVA_ENABLE_URF", "1")
    monkeypatch.setenv("NOVA_ENABLE_MSE", "0")
    monkeypatch.setenv("NOVA_ENABLE_ORP", "1")

    req = types.SimpleNamespace(
        headers={"x-request-id": "r-1", "x-trace-id": "t-1"},
        url=types.SimpleNamespace(path="/router/decide"),
    )

    ctx = app_mod.build_http_decision_context(req)

    assert ctx.request_id == "r-1"
    assert ctx.trace_id == "t-1"
    assert ctx.source == "http:/router/decide"
    assert ctx.flags == {"urf": "1", "mse": "0", "orp": "1"}


@pytest.mark.asyncio
async def test_handle_request_parity_with_control_plane_success(monkeypatch):
    import nova.orchestrator.app as app_mod

    class FakeBus:
        def __init__(self):
            self.events = []

        async def publish(self, topic, event):
            self.events.append((topic, event))
            return []

    class FakeRouter:
        def get_route(self, target_slot, original_timeout=2.0):
            return ("slot02_deltathresh", 3.5)

    captured = []

    async def fake_invoke(slot_fn, slot_name, payload, request_id, timeout=None):
        captured.append(
            {
                "slot_name": slot_name,
                "payload": dict(payload),
                "request_id": request_id,
                "timeout": timeout,
            }
        )
        return {"result": "ok", "slot": slot_name, "timeout": timeout}

    fake_orch = type("FakeOrchestrator", (), {"invoke_slot": staticmethod(fake_invoke)})

    monkeypatch.setattr(app_mod, "bus", FakeBus())
    monkeypatch.setattr(app_mod, "router", FakeRouter())
    monkeypatch.setattr(app_mod, "orch", fake_orch)
    monkeypatch.setattr(app_mod, "SLOT_REGISTRY", {"slot02_deltathresh": object()})

    app_mod.control_plane_factory.configure_execution(
        app_mod.control_plane,
        router=app_mod.router,
        bus=app_mod.bus,
        event_cls=app_mod.Event,
        slot_registry=app_mod.SLOT_REGISTRY,
        orchestrator_runner=app_mod.orch,
    )

    via_app = await app_mod.handle_request("slot02_deltathresh", {"x": 1}, "req-1")
    via_cp = await app_mod.control_plane.handle_request("slot02_deltathresh", {"x": 1}, "req-1")

    assert via_app == via_cp
    assert captured[0] == captured[1]


@pytest.mark.asyncio
async def test_handle_request_parity_with_control_plane_no_runner(monkeypatch):
    import nova.orchestrator.app as app_mod

    class FakeBus:
        async def publish(self, topic, event):
            return []

    class FakeRouter:
        def get_route(self, target_slot, original_timeout=2.0):
            return ("slot02_deltathresh", 2.0)

    monkeypatch.setattr(app_mod, "bus", FakeBus())
    monkeypatch.setattr(app_mod, "router", FakeRouter())
    monkeypatch.setattr(app_mod, "orch", None)
    monkeypatch.setattr(app_mod, "SLOT_REGISTRY", {"slot02_deltathresh": object()})

    app_mod.control_plane_factory.configure_execution(
        app_mod.control_plane,
        router=app_mod.router,
        bus=app_mod.bus,
        event_cls=app_mod.Event,
        slot_registry=app_mod.SLOT_REGISTRY,
        orchestrator_runner=app_mod.orch,
    )

    via_app = await app_mod.handle_request("slot02_deltathresh", {"x": 0}, "req-2")
    via_cp = await app_mod.control_plane.handle_request("slot02_deltathresh", {"x": 0}, "req-2")

    assert via_app == via_cp
    assert via_app.executed is False
    assert via_app.blocked is False
    assert via_app.reason == "no_runner"
    assert via_app.result is None


@pytest.mark.asyncio
async def test_handle_request_parity_with_control_plane_fallback_branch(monkeypatch):
    import nova.orchestrator.app as app_mod

    class FakeBus:
        def __init__(self):
            self.seen_slots = []

        async def publish(self, topic, event):
            self.seen_slots.append(getattr(event, "target_slot", None))
            return []

    class FakeRouter:
        def get_route(self, target_slot, original_timeout=2.0):
            return ("slot08_memory_ethics", 4.0)

    calls = []

    async def fake_invoke(slot_fn, slot_name, payload, request_id, timeout=None):
        calls.append((slot_name, timeout, request_id))
        return {"slot": slot_name, "timeout": timeout}

    fake_orch = type("FakeOrchestrator", (), {"invoke_slot": staticmethod(fake_invoke)})

    monkeypatch.setattr(app_mod, "bus", FakeBus())
    monkeypatch.setattr(app_mod, "router", FakeRouter())
    monkeypatch.setattr(app_mod, "orch", fake_orch)
    monkeypatch.setattr(
        app_mod,
        "SLOT_REGISTRY",
        {
            "slot02_deltathresh": object(),
            "slot08_memory_ethics": object(),
        },
    )

    app_mod.control_plane_factory.configure_execution(
        app_mod.control_plane,
        router=app_mod.router,
        bus=app_mod.bus,
        event_cls=app_mod.Event,
        slot_registry=app_mod.SLOT_REGISTRY,
        orchestrator_runner=app_mod.orch,
    )

    via_app = await app_mod.handle_request("slot02_deltathresh", {"y": 2}, "req-fb")
    via_cp = await app_mod.control_plane.handle_request("slot02_deltathresh", {"y": 2}, "req-fb")

    assert via_app == via_cp
    assert via_app.executed is True
    assert via_app.blocked is False
    assert via_app.reason == "executed"
    assert via_app.slot_id == "slot08_memory_ethics"
    assert via_app.timeout == 4.0
    assert via_app.result == {"slot": "slot08_memory_ethics", "timeout": 4.0}
    assert calls[0] == calls[1]
