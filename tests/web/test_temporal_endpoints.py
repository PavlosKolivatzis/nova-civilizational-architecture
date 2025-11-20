import pytest

pytest.importorskip("fastapi")
from fastapi.testclient import TestClient


def _client():
    from orchestrator.app import app

    return TestClient(app)


def test_temporal_endpoints_available():
    client = _client()
    payload = {
        "tri_signal": {"tri_coherence": 0.9, "tri_drift_z": 0.05, "tri_jitter": 0.02},
        "slot07": {"mode": "BASELINE"},
        "slot10": {"passed": True},
    }
    client.post("/router/decide", json=payload)
    snapshot = client.get("/temporal/snapshot")
    assert snapshot.status_code == 200
    assert snapshot.json()["snapshot"] is not None
    ledger = client.get("/temporal/ledger")
    assert ledger.status_code == 200
    ledger_body = ledger.json()
    assert isinstance(ledger_body["entries"], list)
    debug = client.get("/temporal/debug")
    assert debug.status_code == 200
    body = debug.json()
    assert "entries" in body and "head" in body
