import pytest

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


def test_governance_evaluate_endpoint(monkeypatch):
    client = _client()
    payload = {"tri_signal": {"tri_coherence": 0.2}}
    response = client.post("/governance/evaluate", json=payload)
    assert response.status_code == 200
    body = response.json()
    assert body["allowed"] is False
    assert body["reason"] == "tri_low"


def test_governance_debug_endpoint(monkeypatch):
    client = _client()
    response = client.get("/governance/debug")
    assert response.status_code == 200
    assert "allowed" in response.json()


def test_governance_debug_schema_parity_snapshot(monkeypatch):
    import nova.orchestrator.app as app_mod

    class FakeControlPlane:
        def governance_debug(self):
            return {
                "allowed": True,
                "reason": "ok",
                "ethics": [],
                "snapshot": {"tri_signal": {}},
                "metadata": {"stability_score": 1.0},
            }

    monkeypatch.setattr(app_mod, "control_plane", FakeControlPlane())

    with TestClient(app_mod.app) as client:
        body = client.get("/governance/debug").json()

    assert _schema_snapshot(body) == {
        "allowed": "<bool>",
        "ethics": ["<list>"],
        "metadata": {"stability_score": "<float>"},
        "reason": "<str>",
        "snapshot": {"tri_signal": {}},
    }
