"""Readiness probe integration tests."""

import os
import time

import pytest

pytest.importorskip("fastapi")
from fastapi.testclient import TestClient


def _client() -> TestClient:
    from nova.orchestrator.app import app
    return TestClient(app)


def _setup_metrics():
    from nova.federation.metrics import m

    os.environ["FEDERATION_ENABLED"] = "1"
    metrics = m()
    metrics["peers"].set(1)
    metrics["last_result_ts"].labels(status="success").set(time.time())
    metrics["last_result_ts"].labels(status="error").set(0.0)
    return metrics


def test_ready_returns_200_when_gauge_ready():
    metrics = _setup_metrics()
    metrics["ready"].set(1.0)

    resp = _client().get("/ready")
    assert resp.status_code == 200
    assert resp.json() == {"ready": True}


def test_ready_returns_503_when_gauge_zero():
    metrics = _setup_metrics()
    metrics["ready"].set(0.0)

    resp = _client().get("/ready")
    assert resp.status_code == 503
    assert resp.json() == {"ready": False}
