import pytest

pytest.importorskip("fastapi")
from fastapi.testclient import TestClient


def _client():
    from orchestrator.app import app

    return TestClient(app)


def test_router_metrics_exposed(monkeypatch):
    client = _client()
    monkeypatch.setenv("NOVA_ENABLE_PROMETHEUS", "1")
    payload = {
        "tri_signal": {"tri_coherence": 0.9, "tri_drift_z": 0.1, "tri_jitter": 0.05},
        "slot07": {"mode": "BASELINE"},
        "slot10": {"passed": True},
    }
    client.post("/router/decide", json=payload)
    response = client.get("/metrics/internal")
    assert response.status_code == 200
    text = response.text
    assert "nova_router_final_score" in text
