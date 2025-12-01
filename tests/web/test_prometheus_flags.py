"""Tests for Prometheus feature flag gauges."""

import pytest

pytest.importorskip("fastapi")
from fastapi.testclient import TestClient


def _client():
    from nova.orchestrator.app import app
    return TestClient(app)


def test_flag_gauges_reflect_env(monkeypatch):
    """Test that feature flag gauges reflect environment variables."""
    # Enable /metrics
    monkeypatch.setenv("NOVA_ENABLE_PROMETHEUS", "1")
    # Toggle flags
    monkeypatch.setenv("NOVA_ENABLE_TRI_LINK", "1")
    monkeypatch.setenv("NOVA_ENABLE_LIFESPAN", "0")
    monkeypatch.setenv("NOVA_USE_SHARED_HASH", "1")
    monkeypatch.setenv("FEDERATION_ENABLED", "1")
    monkeypatch.setenv("NOVA_SLOT01_ROOT_MODE", "1")

    r = _client().get("/metrics")
    assert r.status_code == 200
    body = r.text

    assert 'nova_feature_flag_enabled{flag="NOVA_ENABLE_TRI_LINK"} 1' in body
    assert 'nova_feature_flag_enabled{flag="NOVA_ENABLE_LIFESPAN"} 0' in body
    assert 'nova_feature_flag_enabled{flag="NOVA_USE_SHARED_HASH"} 1' in body
    assert 'nova_feature_flag_enabled{flag="NOVA_ENABLE_PROMETHEUS"} 1' in body
    assert 'nova_feature_flag_enabled{flag="FEDERATION_ENABLED"} 1' in body
    assert 'nova_feature_flag_enabled{flag="NOVA_SLOT01_ROOT_MODE"} 1' in body


def test_flag_gauges_all_disabled(monkeypatch):
    """Test flag gauges when all flags are disabled."""
    monkeypatch.setenv("NOVA_ENABLE_PROMETHEUS", "1")
    monkeypatch.setenv("NOVA_ENABLE_TRI_LINK", "0")
    monkeypatch.setenv("NOVA_ENABLE_LIFESPAN", "false")
    monkeypatch.setenv("NOVA_USE_SHARED_HASH", "0")
    monkeypatch.setenv("FEDERATION_ENABLED", "0")
    monkeypatch.setenv("NOVA_SLOT01_ROOT_MODE", "0")

    r = _client().get("/metrics")
    assert r.status_code == 200
    body = r.text

    assert 'nova_feature_flag_enabled{flag="NOVA_ENABLE_TRI_LINK"} 0' in body
    assert 'nova_feature_flag_enabled{flag="NOVA_ENABLE_LIFESPAN"} 0' in body
    assert 'nova_feature_flag_enabled{flag="NOVA_USE_SHARED_HASH"} 0' in body
    assert 'nova_feature_flag_enabled{flag="NOVA_ENABLE_PROMETHEUS"} 1' in body
    assert 'nova_feature_flag_enabled{flag="FEDERATION_ENABLED"} 0' in body
    assert 'nova_feature_flag_enabled{flag="NOVA_SLOT01_ROOT_MODE"} 0' in body


def test_flag_gauges_mixed_values(monkeypatch):
    """Test flag gauges with mixed truthy/falsy values."""
    monkeypatch.setenv("NOVA_ENABLE_PROMETHEUS", "1")
    monkeypatch.setenv("NOVA_ENABLE_TRI_LINK", "1")
    monkeypatch.setenv("NOVA_ENABLE_LIFESPAN", "")
    monkeypatch.setenv("NOVA_USE_SHARED_HASH", "1")
    monkeypatch.setenv("FEDERATION_ENABLED", "1")
    monkeypatch.setenv("NOVA_SLOT01_ROOT_MODE", "1")

    r = _client().get("/metrics")
    assert r.status_code == 200
    body = r.text

    assert 'nova_feature_flag_enabled{flag="NOVA_ENABLE_TRI_LINK"} 1' in body
    assert 'nova_feature_flag_enabled{flag="NOVA_ENABLE_LIFESPAN"} 0' in body
    assert 'nova_feature_flag_enabled{flag="NOVA_USE_SHARED_HASH"} 1' in body
    assert 'nova_feature_flag_enabled{flag="NOVA_ENABLE_PROMETHEUS"} 1' in body
    assert 'nova_feature_flag_enabled{flag="FEDERATION_ENABLED"} 1' in body
    assert 'nova_feature_flag_enabled{flag="NOVA_SLOT01_ROOT_MODE"} 1' in body


def test_flag_gauges_with_slot7_fallback(monkeypatch):
    """Test that flag gauges work with env fallback when Slot7 is unavailable."""
    monkeypatch.setenv("NOVA_ENABLE_PROMETHEUS", "1")
    monkeypatch.setenv("NOVA_ENABLE_TRI_LINK", "1")
    monkeypatch.setenv("NOVA_ENABLE_LIFESPAN", "1")
    monkeypatch.setenv("NOVA_USE_SHARED_HASH", "0")
    monkeypatch.setenv("FEDERATION_ENABLED", "1")
    monkeypatch.setenv("NOVA_SLOT01_ROOT_MODE", "1")

    # Even if Slot7 import fails, env fallback should work
    r = _client().get("/metrics")
    assert r.status_code == 200
    body = r.text

    # Should have all six flag gauges
    assert body.count('nova_feature_flag_enabled{flag="') == 6
    assert 'nova_feature_flag_enabled{flag="NOVA_ENABLE_TRI_LINK"} 1' in body
    assert 'nova_feature_flag_enabled{flag="NOVA_ENABLE_LIFESPAN"} 1' in body
    assert 'nova_feature_flag_enabled{flag="NOVA_USE_SHARED_HASH"} 0' in body
    assert 'nova_feature_flag_enabled{flag="NOVA_ENABLE_PROMETHEUS"} 1' in body
    assert 'nova_feature_flag_enabled{flag="FEDERATION_ENABLED"} 1' in body
    assert 'nova_feature_flag_enabled{flag="NOVA_SLOT01_ROOT_MODE"} 1' in body


def test_internal_metrics_endpoint(monkeypatch):
    """Internal metrics endpoint exposes extended gauges."""
    monkeypatch.setenv("NOVA_ENABLE_PROMETHEUS", "1")
    monkeypatch.setenv("NOVA_SLOT01_ROOT_MODE", "1")

    r = _client().get("/metrics/internal")
    assert r.status_code == 200
    assert 'nova_feature_flag_enabled{flag="NOVA_SLOT01_ROOT_MODE"} 1' in r.text
