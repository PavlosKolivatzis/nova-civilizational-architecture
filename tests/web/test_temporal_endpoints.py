import pytest

pytest.importorskip("fastapi")
from fastapi.testclient import TestClient


def _client():
    from orchestrator.app import app

    return TestClient(app)


def test_temporal_endpoints_available():
    client = _client()
    assert client.get("/temporal/snapshot").status_code == 200
    res = client.get("/temporal/ledger")
    assert res.status_code == 200
    assert "entries" in res.json()
