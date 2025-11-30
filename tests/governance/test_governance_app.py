import pytest

pytest.importorskip("fastapi")
from fastapi.testclient import TestClient


def _client():
    from nova.orchestrator.app import app

    return TestClient(app)


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
