import pytest

pytest.importorskip("fastapi")
from fastapi.testclient import TestClient


def _client():
    from orchestrator.app import app

    return TestClient(app)


def test_predictive_metrics_endpoint(monkeypatch):
    monkeypatch.setenv("NOVA_ENABLE_PROMETHEUS", "1")
    client = _client()
    client.post(
        "/router/decide",
        json={
            "tri_signal": {"tri_coherence": 0.9, "tri_drift_z": 0.1, "tri_jitter": 0.05},
            "slot07": {"mode": "BASELINE"},
            "slot10": {"passed": True},
        },
    )
    response = client.get("/metrics/predictive")
    assert response.status_code == 200
    body = response.text
    assert "nova_predictive_collapse_risk" in body
    assert "nova_predictive_penalty" in body
