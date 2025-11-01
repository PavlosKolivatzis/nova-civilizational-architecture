import os
import time

import pytest

pytest.importorskip("fastapi")
from fastapi.testclient import TestClient


def _client():
    from orchestrator.app import app
    return TestClient(app)


def _setup_metrics():
    from nova.federation import metrics

    os.environ["FEDERATION_ENABLED"] = "1"
    return metrics.m()


def test_ready_when_metric_ready(monkeypatch):
    data = _setup_metrics()
    now = time.time()
    data["ready"].set(1.0)
    data["peers"].set(1)
    data["last_result_ts"].labels(status="success").set(now)

    resp = _client().get("/ready")
    assert resp.status_code == 200
    assert resp.json()["ready"] is True


def test_ready_when_metric_absent(monkeypatch):
    from orchestrator import federation_health

    def boom():
        raise RuntimeError("boom")

    monkeypatch.setattr(federation_health, "get_peer_health", boom)

    resp = _client().get("/ready")
    assert resp.status_code == 503
    assert resp.json()["ready"] is False


def test_ready_when_gauge_not_ready():
    data = _setup_metrics()
    data["ready"].set(0.0)
    data["peers"].set(1)
    data["last_result_ts"].labels(status="success").set(time.time())

    resp = _client().get("/ready")
    assert resp.status_code == 503
    assert resp.json()["ready"] is False
