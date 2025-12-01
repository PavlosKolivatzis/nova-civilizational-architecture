import os
import time

import pytest

pytest.importorskip("fastapi")
from fastapi.testclient import TestClient


def _client():
    from nova.orchestrator.app import app
    return TestClient(app)


def test_federation_health_payload():
    from nova.federation import metrics

    os.environ["FEDERATION_ENABLED"] = "1"
    data = metrics.m()
    now = time.time()
    data["ready"].set(1.0)
    data["peers"].set(2)
    data["height"].set(55)
    data["last_result_ts"].labels(status="success").set(now)
    data["last_result_ts"].labels(status="error").set(0.0)
    data["peer_up"].labels(peer="node-a").set(1.0)
    data["peer_last_seen"].labels(peer="node-a").set(now - 5)

    resp = _client().get("/federation/health")
    assert resp.status_code == 200
    payload = resp.json()
    assert isinstance(payload, dict)
    assert payload["ready"] is True
    assert payload["checkpoint"]["height"] == 55
    assert payload["peers"][0]["id"] == "node-a"
    assert payload["peers"][0]["state"] == "up"


def test_federation_health_handles_exception(monkeypatch):
    from nova.orchestrator import federation_health

    def boom():
        raise RuntimeError("broken")

    monkeypatch.setattr(federation_health, "get_peer_health", boom)
    resp = _client().get("/federation/health")
    assert resp.status_code == 503
