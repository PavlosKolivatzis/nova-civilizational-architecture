import pytest

pytest.importorskip("fastapi")
from fastapi.testclient import TestClient


def _client():
    from orchestrator.app import app

    return TestClient(app)


def test_temporal_metrics_endpoint(monkeypatch):
    monkeypatch.setenv("NOVA_ENABLE_PROMETHEUS", "1")
    client = _client()
    response = client.get("/metrics/temporal")
    assert response.status_code == 200
    assert "nova_temporal_router_state" in response.text
