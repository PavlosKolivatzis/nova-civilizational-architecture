"""Tests for public/internal Prometheus endpoints."""

import pytest

pytest.importorskip("fastapi")
from fastapi.testclient import TestClient


def _client():
    from orchestrator.app import app

    return TestClient(app)


def test_public_metrics_available(monkeypatch):
    monkeypatch.setenv("NOVA_ENABLE_PROMETHEUS", "1")
    response = _client().get("/metrics")
    assert response.status_code == 200
    assert "python_gc_objects_collected_total" in response.text


def test_internal_metrics_available(monkeypatch):
    monkeypatch.setenv("NOVA_ENABLE_PROMETHEUS", "1")
    response = _client().get("/metrics/internal")
    assert response.status_code == 200
    assert "nova_tri_coherence" in response.text
