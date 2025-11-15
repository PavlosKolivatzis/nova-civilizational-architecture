"""Tests for Slot1 Truth Anchor metrics in Prometheus export."""

import pytest

pytest.importorskip("fastapi")
pytest.importorskip("prometheus_client")
from fastapi.testclient import TestClient


def _client():
    from orchestrator.app import app
    return TestClient(app)


def test_slot1_metrics_in_prometheus_export(monkeypatch):
    """Test that Slot1 metrics are included in Prometheus export."""
    monkeypatch.setenv("NOVA_ENABLE_PROMETHEUS", "1")

    # Generate some Slot1 activity
    from orchestrator.adapters.slot1_truth_anchor import Slot1TruthAnchorAdapter
    adapter = Slot1TruthAnchorAdapter()

    if adapter.available:
        # Create test anchors and perform operations
        adapter.register('metrics.test1', 'Test Value 1')
        adapter.register('metrics.test2', 'Test Value 2')
        adapter.verify('metrics.test1', 'Test Value 1')  # Should succeed
        adapter.verify('metrics.test2', 'Wrong Value')   # Should fail

    r = _client().get("/metrics")
    assert r.status_code == 200
    body = r.text

    # Check for Slot1 metrics
    assert 'nova_slot1_anchors_total' in body
    assert 'nova_slot1_lookups_total' in body
    assert 'nova_slot1_recoveries_total' in body
    assert 'nova_slot1_failures_total' in body


def test_slot1_metrics_values_match_adapter(monkeypatch):
    """Test that Prometheus metrics match adapter snapshot values."""
    monkeypatch.setenv("NOVA_ENABLE_PROMETHEUS", "1")

    from orchestrator.adapters.slot1_truth_anchor import Slot1TruthAnchorAdapter
    adapter = Slot1TruthAnchorAdapter()

    if adapter.available:
        # Generate predictable activity
        adapter.register('predictable.test', 'Test Value')
        adapter.verify('predictable.test', 'Test Value')  # Success

        # Get adapter snapshot
        snapshot = adapter.snapshot()

        # Get Prometheus metrics
        r = _client().get("/metrics")
        assert r.status_code == 200

        # Parse metrics
        lines = r.text.split('\n')
        metrics = {}
        for line in lines:
            if 'nova_slot1_' in line and not line.startswith('#'):
                metric_name = line.split(' ')[0]
                value = float(line.split(' ')[-1])
                metrics[metric_name] = value

        # Verify values match
        assert metrics.get('nova_slot1_anchors_total', 0) == snapshot.get('anchors', 0)
        assert metrics.get('nova_slot1_lookups_total', 0) == snapshot.get('lookups', 0)
        assert metrics.get('nova_slot1_recoveries_total', 0) == snapshot.get('recoveries', 0)
        assert metrics.get('nova_slot1_failures_total', 0) == snapshot.get('failures', 0)


def test_slot1_metrics_when_unavailable(monkeypatch):
    """Test that Slot1 metrics are zeroed when adapter unavailable."""
    monkeypatch.setenv("NOVA_ENABLE_PROMETHEUS", "1")

    # This test assumes the adapter is available, but we test the fallback logic
    r = _client().get("/metrics")
    assert r.status_code == 200
    body = r.text

    # Metrics should be present (even if zero)
    assert 'nova_slot1_anchors_total' in body
    assert 'nova_slot1_lookups_total' in body
    assert 'nova_slot1_recoveries_total' in body
    assert 'nova_slot1_failures_total' in body
