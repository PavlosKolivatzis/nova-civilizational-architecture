"""Tests for ledger-federation correlation (Phase 15-7)."""

import time
from unittest.mock import MagicMock, patch

import pytest

from nova.federation.metrics import get_registry, m


@pytest.fixture(autouse=True)
def reset_metrics():
    """Reset metrics registry before each test."""
    from nova.federation import metrics

    metrics._registry = None
    metrics._metrics.clear()
    yield
    metrics._registry = None
    metrics._metrics.clear()


def test_ledger_reader_http_url(monkeypatch):
    """Test get_ledger_status with HTTP URL."""
    from nova.orchestrator.ledger_reader import get_ledger_status
    from urllib import request

    mock_response = MagicMock()
    mock_response.read.return_value = b'{"height": 100, "head_ts": 1234567890.0}'
    mock_response.__enter__ = lambda self: self
    mock_response.__exit__ = lambda *args: None

    with patch.object(request, "urlopen", return_value=mock_response):
        monkeypatch.setenv("NOVA_LEDGER_STATUS_URL", "http://localhost:8080/ledger/status")
        monkeypatch.delenv("NOVA_LEDGER_STATUS_CMD", raising=False)

        result = get_ledger_status(timeout=2.0)

        assert result["height"] == 100
        assert result["head_age"] > 0  # Should be non-zero since head_ts is in the past


def test_ledger_reader_shell_command(monkeypatch):
    """Test get_ledger_status with shell command."""
    import subprocess

    from nova.orchestrator.ledger_reader import get_ledger_status

    now = time.time()
    mock_result = MagicMock()
    mock_result.returncode = 0
    mock_result.stdout = f'{{"height": 120, "head_ts": {now}}}'

    with patch.object(subprocess, "run", return_value=mock_result):
        monkeypatch.delenv("NOVA_LEDGER_STATUS_URL", raising=False)
        monkeypatch.setenv("NOVA_LEDGER_STATUS_CMD", "echo test")

        result = get_ledger_status(timeout=2.0)

        assert result["height"] == 120
        assert result["head_age"] >= 0
        assert result["head_age"] < 1.0  # Should be very recent


def test_ledger_reader_fallback():
    """Test get_ledger_status returns zero values on error."""
    import os

    from nova.orchestrator.ledger_reader import get_ledger_status

    # Clear any env vars
    os.environ.pop("NOVA_LEDGER_STATUS_URL", None)
    os.environ.pop("NOVA_LEDGER_STATUS_CMD", None)

    result = get_ledger_status(timeout=2.0)

    assert result == {"height": 0, "head_age": 0.0}


def test_get_last_ledger_accessor():
    """Test get_last_ledger returns cached state."""
    from nova.orchestrator.federation_poller import _LAST_LEDGER, get_last_ledger

    # Directly set the cache
    _LAST_LEDGER["height"] = 100
    _LAST_LEDGER["head_age"] = 42.0
    _LAST_LEDGER["gap"] = 20

    result = get_last_ledger()

    assert result["height"] == 100
    assert result["head_age"] == 42.0
    assert result["gap"] == 20
    # Verify it returns a copy, not the original
    result["height"] = 999
    assert _LAST_LEDGER["height"] == 100


def test_health_endpoint_includes_ledger():
    """Test /federation/health includes ledger field."""
    from nova.orchestrator.federation_health import get_peer_health
    from nova.orchestrator.federation_poller import _LAST_LEDGER

    # Set up ledger state
    _LAST_LEDGER["height"] = 100
    _LAST_LEDGER["head_age"] = 42.0
    _LAST_LEDGER["gap"] = 20

    # Initialize metrics
    m()

    health = get_peer_health()

    assert "ledger" in health
    assert health["ledger"]["height"] == 100
    assert health["ledger"]["head_age"] == 42.0
    assert health["ledger"]["gap"] == 20


def test_ledger_metrics_initialized():
    """Test ledger metrics are initialized on startup."""
    metrics = m()

    assert "ledger_height" in metrics
    assert "ledger_head_age" in metrics
    assert "ledger_federation_gap" in metrics
    assert "ledger_federation_gap_abs" in metrics

    # Check initial values are zero
    assert metrics["ledger_height"]._value.get() == 0
    assert metrics["ledger_head_age"]._value.get() == 0.0
    assert metrics["ledger_federation_gap"]._value.get() == 0
    assert metrics["ledger_federation_gap_abs"]._value.get() == 0
