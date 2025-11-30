
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

    assert result == {"result": "ok"}
    assert captured["slot_name"] == "slot02_deltathresh"
    assert captured["payload"] == {"payload": True}
    assert captured["request_id"] == "req-123"
    assert captured["timeout"] == 3.5


@pytest.mark.asyncio
async def test_handle_request_no_orchestrator_returns_none(monkeypatch):
    import nova.orchestrator.app as app_mod

    monkeypatch.setattr(
        app_mod.router,
        "get_route",
        lambda target_slot, original_timeout=2.0: ("slot02_deltathresh", 2.0),
    )
    monkeypatch.setattr(app_mod, "orch", None)
    result = await app_mod.handle_request("slot02_deltathresh", {"payload": False}, "req-999")
    assert result is None


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
        "orchestrator.prometheus_metrics.get_metrics_response",
        lambda: (b"metrics-data", "text/custom"),
    )
    with TestClient(app_module.app) as client:
        resp = client.get("/metrics")
        assert resp.status_code == 200
        assert resp.content == b"metrics-data"
        assert resp.headers["content-type"].startswith("text/custom")


def test_force_expire_now_uses_semantic_mirror(app_module, monkeypatch):
    monkeypatch.setenv("NOVA_ALLOW_EXPIRE_TEST", "1")
    monkeypatch.setattr(
        "orchestrator.prometheus_metrics.update_semantic_mirror_metrics", lambda: None
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
    monkeypatch.setattr("orchestrator.semantic_mirror.ContextScope", DummyScope)
    monkeypatch.setattr("orchestrator.semantic_mirror.get_semantic_mirror", lambda: stub)

    with TestClient(app_module.app) as client:
        resp = client.post("/ops/expire-now")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "ok"
        assert data["expired_count"] >= 1
        assert data["pulses_delta"] >= 1
