import pytest

pytest.importorskip("fastapi")
from fastapi.testclient import TestClient


def _client():
    from nova.orchestrator.app import app

    return TestClient(app)


def test_router_decide_blocks_when_governance_fails(monkeypatch):
    client = _client()
    payload = {
        "tri_signal": {"tri_coherence": 0.1},
        "slot07": {"mode": "BASELINE"},
        "slot10": {"passed": True},
    }
    response = client.post("/router/decide", json=payload)
    assert response.status_code == 200
    body = response.json()
    assert body["route"] == "hold"
    assert body["governance"]["allowed"] is False
