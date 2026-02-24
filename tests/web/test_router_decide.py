import pytest
from nova.orchestrator.control_plane import DecisionResponseEnvelope

pytest.importorskip("fastapi")
from fastapi.testclient import TestClient


def _client():
    from nova.orchestrator.app import app

    return TestClient(app)


def _schema_snapshot(value):
    if isinstance(value, dict):
        return {k: _schema_snapshot(v) for k, v in sorted(value.items())}
    if isinstance(value, list):
        return ["<list>"] if not value else [_schema_snapshot(value[0])]
    return f"<{type(value).__name__}>"


def test_router_decide_endpoint(monkeypatch):
    client = _client()
    payload = {
        "tri_signal": {"tri_coherence": 0.9, "tri_drift_z": 0.1, "tri_jitter": 0.05},
        "slot07": {"mode": "BASELINE"},
        "slot10": {"passed": True},
        "risk": 0.2,
        "novelty": 0.6,
    }
    response = client.post("/router/decide", json=payload)
    assert response.status_code == 200
    body = response.json()
    assert "route" in body
    if body["route"] == "hold":
        assert "governance" in body
    else:
        assert "constraints" in body
        assert "policy" in body
    if "metadata" in body and isinstance(body["metadata"], dict):
        temporal_meta = body["metadata"].get("temporal")
        if temporal_meta:
            assert "allowed" in temporal_meta


def test_router_debug_endpoint(monkeypatch):
    client = _client()
    response = client.get("/router/debug")
    assert response.status_code == 200
    body = response.json()
    assert "metadata" in body
    assert body["metadata"]["mode"] == "deterministic"


def test_router_debug_schema_parity_snapshot(monkeypatch):
    import nova.orchestrator.app as app_mod

    class FakeControlPlane:
        def router_debug(self):
            return {
                "route": "primary",
                "constraints": {"allowed": True, "reasons": [], "snapshot": {}},
                "policy": {"route": "primary", "score": 0.7, "details": {}},
                "advisors": {},
                "final_score": 0.7,
                "metadata": {"predictive": {}, "mode": "deterministic"},
                "governance": {
                    "allowed": True,
                    "reason": "ok",
                    "ethics": [],
                    "snapshot": {},
                    "metadata": {},
                },
            }

    monkeypatch.setattr(app_mod, "control_plane", FakeControlPlane())

    with TestClient(app_mod.app) as client:
        body = client.get("/router/debug").json()

    assert _schema_snapshot(body) == {
        "advisors": {},
        "constraints": {"allowed": "<bool>", "reasons": ["<list>"], "snapshot": {}},
        "final_score": "<float>",
        "governance": {
            "allowed": "<bool>",
            "ethics": ["<list>"],
            "metadata": {},
            "reason": "<str>",
            "snapshot": {},
        },
        "metadata": {"mode": "<str>", "predictive": {}},
        "policy": {"details": {}, "route": "<str>", "score": "<float>"},
        "route": "<str>",
    }


def test_router_decide_delegates_context_to_control_plane(monkeypatch):
    import nova.orchestrator.app as app_mod

    captured = {}
    original = app_mod.control_plane

    def fake_decide_http(payload, request):
        captured["payload"] = dict(payload)
        captured["request"] = request
        return {
            "route": "hold",
            "governance": {"allowed": False, "reason": "test"},
            "constraints": {"allowed": False, "reasons": ["test"], "snapshot": {}},
        }

    monkeypatch.setattr(original, "decide_http", fake_decide_http)
    with TestClient(app_mod.app) as client:
        resp = client.post(
            "/router/decide",
            json={"risk": 0.3},
            headers={"x-request-id": "req-42", "x-trace-id": "trace-42"},
        )

    assert resp.status_code == 200
    assert captured["payload"] == {"risk": 0.3}
    req = captured["request"]
    assert req.headers["x-request-id"] == "req-42"
    assert req.headers["x-trace-id"] == "trace-42"
    assert req.url.path == "/router/decide"


def test_router_decide_hold_schema_parity_snapshot(monkeypatch):
    import nova.orchestrator.app as app_mod

    class FakeControlPlane:
        def decide_http(self, payload, request):
            return DecisionResponseEnvelope.hold(
                governance={
                    "allowed": False,
                    "reason": "tri_low",
                    "ethics": [],
                    "snapshot": {},
                    "metadata": {},
                }
            ).to_dict()

    monkeypatch.setattr(app_mod, "control_plane", FakeControlPlane())
    with TestClient(app_mod.app) as client:
        body = client.post("/router/decide", json={"tri_signal": {"tri_coherence": 0.1}}).json()

    assert _schema_snapshot(body) == {
        "constraints": {
            "allowed": "<bool>",
            "reasons": ["<str>"],
            "snapshot": {},
        },
        "governance": {
            "allowed": "<bool>",
            "ethics": ["<list>"],
            "metadata": {},
            "reason": "<str>",
            "snapshot": {},
        },
        "route": "<str>",
    }


def test_router_decide_routed_schema_parity_snapshot(monkeypatch):
    import nova.orchestrator.app as app_mod

    class FakeControlPlane:
        def decide_http(self, payload, request):
            return DecisionResponseEnvelope.routed(
                decision={
                    "route": "primary",
                    "constraints": {"allowed": True, "reasons": [], "snapshot": {"tri_signal": {}}},
                    "policy": {"route": "primary", "score": 0.8, "details": {"risk": 0.2}},
                    "advisors": {"slot05": {"name": "slot05", "score": 0.9, "details": {}}},
                    "final_score": 0.72,
                    "metadata": {"mode": "deterministic", "predictive": {"predictive_allowed": True}},
                },
                governance={
                    "allowed": True,
                    "reason": "ok",
                    "ethics": [],
                    "snapshot": {},
                    "metadata": {},
                },
            ).to_dict()

    monkeypatch.setattr(app_mod, "control_plane", FakeControlPlane())
    with TestClient(app_mod.app) as client:
        body = client.post("/router/decide", json={"risk": 0.2, "novelty": 0.6}).json()

    assert _schema_snapshot(body) == {
        "advisors": {
            "slot05": {
                "details": {},
                "name": "<str>",
                "score": "<float>",
            }
        },
        "constraints": {
            "allowed": "<bool>",
            "reasons": ["<list>"],
            "snapshot": {"tri_signal": {}},
        },
        "final_score": "<float>",
        "governance": {
            "allowed": "<bool>",
            "ethics": ["<list>"],
            "metadata": {},
            "reason": "<str>",
            "snapshot": {},
        },
        "metadata": {
            "mode": "<str>",
            "predictive": {"predictive_allowed": "<bool>"},
        },
        "policy": {
            "details": {"risk": "<float>"},
            "route": "<str>",
            "score": "<float>",
        },
        "route": "<str>",
    }


def test_router_decide_serializer_contract_snapshot_hold():
    body = DecisionResponseEnvelope.hold(
        {"allowed": False, "reason": "tri_low", "ethics": [], "snapshot": {}, "metadata": {}}
    ).to_dict()

    assert _schema_snapshot(body) == {
        "constraints": {"allowed": "<bool>", "reasons": ["<str>"], "snapshot": {}},
        "governance": {
            "allowed": "<bool>",
            "ethics": ["<list>"],
            "metadata": {},
            "reason": "<str>",
            "snapshot": {},
        },
        "route": "<str>",
    }


def test_router_decide_serializer_contract_snapshot_routed():
    body = DecisionResponseEnvelope.routed(
        decision={
            "route": "primary",
            "constraints": {"allowed": True, "reasons": [], "snapshot": {"tri_signal": {}}},
            "policy": {"route": "primary", "score": 0.8, "details": {"risk": 0.2}},
            "advisors": {"slot05": {"name": "slot05", "score": 0.9, "details": {}}},
            "final_score": 0.72,
            "metadata": {"mode": "deterministic", "predictive": {"predictive_allowed": True}},
        },
        governance={"allowed": True, "reason": "ok", "ethics": [], "snapshot": {}, "metadata": {}},
    ).to_dict()

    assert _schema_snapshot(body) == {
        "advisors": {
            "slot05": {"details": {}, "name": "<str>", "score": "<float>"},
        },
        "constraints": {"allowed": "<bool>", "reasons": ["<list>"], "snapshot": {"tri_signal": {}}},
        "final_score": "<float>",
        "governance": {
            "allowed": "<bool>",
            "ethics": ["<list>"],
            "metadata": {},
            "reason": "<str>",
            "snapshot": {},
        },
        "metadata": {"mode": "<str>", "predictive": {"predictive_allowed": "<bool>"}},
        "policy": {"details": {"risk": "<float>"}, "route": "<str>", "score": "<float>"},
        "route": "<str>",
    }
