import pytest

pytest.importorskip("fastapi")
from fastapi.testclient import TestClient


def _client():
    from nova.orchestrator.app import app

    return TestClient(app)


def test_predictive_ledger_endpoint(monkeypatch):
    client = _client()
    # Generate a predictive entry by forcing routing/gov evaluation
    client.post(
        "/router/decide",
        json={
            "tri_signal": {"tri_coherence": 0.9, "tri_drift_z": 0.1, "tri_jitter": 0.05},
            "slot07": {"mode": "BASELINE"},
            "slot10": {"passed": True},
        },
    )
    res = client.get("/predictive/ledger")
    assert res.status_code == 200
    body = res.json()
    assert "entries" in body
    assert isinstance(body["entries"], list)
