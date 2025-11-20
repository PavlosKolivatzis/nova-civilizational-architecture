import pytest

pytest.importorskip("fastapi")
from fastapi.testclient import TestClient


def _client():
    from orchestrator.app import app

    return TestClient(app)


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
    assert "constraints" in body
    assert "policy" in body


def test_router_debug_endpoint(monkeypatch):
    client = _client()
    response = client.get("/router/debug")
    assert response.status_code == 200
    body = response.json()
    assert "metadata" in body
    assert body["metadata"]["mode"] == "deterministic"
