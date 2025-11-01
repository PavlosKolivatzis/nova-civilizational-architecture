"""Peer health endpoint contract tests."""

import os
import time

import pytest

pytest.importorskip("fastapi")
from fastapi.testclient import TestClient


def _client() -> TestClient:
    from orchestrator.app import app
    return TestClient(app)


def test_peer_health_schema():
    from nova.federation.metrics import m

    os.environ["FEDERATION_ENABLED"] = "1"
    metrics = m()
    now = time.time()
    metrics["ready"].set(1.0)
    metrics["peers"].set(2)
    metrics["height"].set(42)
    metrics["last_result_ts"].labels(status="success").set(now)
    metrics["peer_up"].labels(peer="node-a").set(1.0)
    metrics["peer_last_seen"].labels(peer="node-a").set(now - 5)
    metrics["peer_up"].labels(peer="node-b").set(0.0)
    metrics["peer_last_seen"].labels(peer="node-b").set(0.0)

    resp = _client().get("/federation/health")
    assert resp.status_code == 200
    payload = resp.json()

    assert payload["ready"] is True
    assert payload["checkpoint"]["height"] == 42
    assert payload["peers"][0]["id"] == "node-a"
    assert payload["peers"][0]["state"] == "up"
    assert payload["peers"][1]["id"] == "node-b"
    assert payload["peers"][1]["state"] == "unknown"
