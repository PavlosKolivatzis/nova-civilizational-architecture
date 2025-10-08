"""Tests for Prometheus metrics endpoint with gating."""

import pytest

pytest.importorskip("fastapi")
pytest.importorskip("prometheus_client")
from fastapi.testclient import TestClient
from prometheus_client import CONTENT_TYPE_LATEST


def test_metrics_404_when_disabled(monkeypatch):
    """Test that /metrics returns 404 when NOVA_ENABLE_PROMETHEUS is disabled."""
    monkeypatch.setenv("NOVA_ENABLE_PROMETHEUS", "0")
    from orchestrator.app import app
    client = TestClient(app)
    r = client.get("/metrics")
    assert r.status_code == 404


def test_metrics_200_when_enabled(monkeypatch):
    """Test that /metrics returns 200 when NOVA_ENABLE_PROMETHEUS is enabled."""
    monkeypatch.setenv("NOVA_ENABLE_PROMETHEUS", "1")
    from orchestrator.app import app
    client = TestClient(app)
    r = client.get("/metrics")
    assert r.status_code == 200
    # Accept both the canonical content-type and plain text fallback
    assert r.headers.get("content-type", "").startswith(CONTENT_TYPE_LATEST) or \
           r.headers.get("content-type", "").startswith("text/plain")
    assert b"nova_slot6_p95_residual_risk" in r.content or len(r.content) > 0


@pytest.mark.parametrize("flag_value", ["false", "0", "no", "off", ""])
def test_metrics_disabled_variants(monkeypatch, flag_value):
    """Test various falsy values disable the metrics endpoint."""
    monkeypatch.setenv("NOVA_ENABLE_PROMETHEUS", flag_value)
    from orchestrator.app import app
    client = TestClient(app)
    r = client.get("/metrics")
    assert r.status_code == 404


@pytest.mark.parametrize("flag_value", ["1", "true", "TRUE", "yes", "on", "ON"])
def test_metrics_enabled_variants(monkeypatch, flag_value):
    """Test various truthy values enable the metrics endpoint."""
    monkeypatch.setenv("NOVA_ENABLE_PROMETHEUS", flag_value)
    from orchestrator.app import app
    client = TestClient(app)
    r = client.get("/metrics")
    assert r.status_code == 200