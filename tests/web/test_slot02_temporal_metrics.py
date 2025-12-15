"""Tests for Slot02 temporal USM Prometheus metrics."""

import pytest

pytest.importorskip("fastapi")
pytest.importorskip("prometheus_client")

from fastapi.testclient import TestClient


def _client():
    from nova.orchestrator.app import app

    return TestClient(app)


def test_slot02_temporal_metrics_export(monkeypatch):
    """record_slot02_temporal_metrics emits gauges visible at /metrics/internal."""
    monkeypatch.setenv("NOVA_ENABLE_PROMETHEUS", "1")
    monkeypatch.setenv("NOVA_ENABLE_BIAS_DETECTION", "1")
    monkeypatch.setenv("NOVA_ENABLE_USM_TEMPORAL", "1")

    from nova.orchestrator.prometheus_metrics import record_slot02_temporal_metrics

    session_id = "test-session-slot02"
    bias_report = {"extraction_present": True}
    temporal_usm = {
        "rho_temporal": 0.15,
        "C_temporal": 0.22,
        "graph_state": "normal",
        "turn_count": 5,
        "temporal_state": "active",
    }

    # Use a small min_turns for deterministic fallback, though temporal_state is provided.
    record_slot02_temporal_metrics(
        session_id=session_id,
        bias_report=bias_report,
        temporal_usm=temporal_usm,
        min_turns=3,
    )

    client = _client()
    resp = client.get("/metrics/internal")
    assert resp.status_code == 200
    body = resp.text

    # Check that all four Slot02 temporal metrics are present.
    assert "nova_extraction_present" in body
    assert "nova_rho_temporal" in body
    assert "nova_coherence_temporal" in body
    assert "nova_temporal_state" in body

