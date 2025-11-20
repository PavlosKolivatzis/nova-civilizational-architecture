import pytest

pytest.importorskip("fastapi")
from fastapi.testclient import TestClient


def _client():
    from orchestrator.app import app

    return TestClient(app)


def _seed_temporal_metrics(client: TestClient) -> None:
    payload = {
        "tri_signal": {"tri_coherence": 0.92, "tri_drift_z": 0.1, "tri_jitter": 0.05},
        "slot07": {"mode": "BASELINE"},
        "slot10": {"passed": True},
    }
    client.post("/router/decide", json=payload)


def test_temporal_metrics_endpoint(monkeypatch):
    monkeypatch.setenv("NOVA_ENABLE_PROMETHEUS", "1")
    client = _client()
    _seed_temporal_metrics(client)
    response = client.get("/metrics/temporal")
    assert response.status_code == 200
    assert "nova_temporal_router_state" in response.text


def test_internal_metrics_surface_temporal_gauges(monkeypatch):
    monkeypatch.setenv("NOVA_ENABLE_PROMETHEUS", "1")
    client = _client()
    _seed_temporal_metrics(client)
    response = client.get("/metrics/internal")
    assert response.status_code == 200
    body = response.text
    for metric in (
        "nova_temporal_drift",
        "nova_temporal_variance",
        "nova_temporal_prediction_error",
        "nova_temporal_convergence",
        "nova_temporal_divergence",
    ):
        assert metric in body
