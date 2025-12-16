import pytest

pytest.importorskip("fastapi")

from fastapi.testclient import TestClient


def _client():
    from nova.orchestrator.app import app

    return TestClient(app)


def test_dev_slot02_endpoint_basic(monkeypatch):
    """Dev Slot02 endpoint exists and returns basic structure."""
    client = _client()

    payload = {"content": "test content for slot02", "session_id": "dev-rt-001"}
    resp = client.post("/dev/slot02", json=payload)

    # Slot02 may or may not be available depending on environment;
    # only assert that the endpoint behaves coherently.
    if resp.status_code == 503:
        # slot02_deltathresh unavailable; this is acceptable for this test.
        assert "unavailable" in resp.json().get("detail", "").lower()
    else:
        assert resp.status_code == 200
        body = resp.json()
        assert body["session_id"] == "dev-rt-001"
        assert "bias_report" in body
        assert "temporal_usm" in body

