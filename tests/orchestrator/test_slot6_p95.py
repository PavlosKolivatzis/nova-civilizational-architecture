"""Tests for Slot6 p95 residual risk tracking."""

import pytest
import threading
from nova.orchestrator.metrics import Slot6Metrics


@pytest.mark.health
def test_p95_residual_risk_monotonic_window():
    """Test p95 calculation with monotonic data."""
    m = Slot6Metrics(window=64)
    # 1..100 mapped to 0..1
    for i in range(1, 101):
        m.record_decision("test_decision", 0.8, i / 100.0)

    p95 = m.p95_residual_risk()
    assert p95 is not None
    # For 100 values in window=64, we keep values 37-100 (0.37-1.0)
    # p95 of that range should be ~0.968
    assert 0.96 <= p95 <= 0.98, f"unexpected p95={p95}"


def test_p95_empty_data():
    """Test p95 returns None for empty data."""
    m = Slot6Metrics(window=16)
    assert m.p95_residual_risk() is None


def test_p95_single_value():
    """Test p95 with single data point."""
    m = Slot6Metrics(window=16)
    m.record_decision("test", 0.8, 0.5)

    p95 = m.p95_residual_risk()
    assert p95 == 0.5


def test_rolling_window_behavior():
    """Test that window properly limits data."""
    m = Slot6Metrics(window=4)

    # Fill beyond window size
    for i in range(1, 7):  # 6 values, window=4
        m.record_decision("test", 0.8, i / 10.0)

    # Should only have last 4 values: [0.3, 0.4, 0.5, 0.6]
    p95 = m.p95_residual_risk()
    assert p95 is not None
    assert 0.55 <= p95 <= 0.6  # p95 of [0.3,0.4,0.5,0.6] should be ~0.585


def test_get_metrics_includes_p95():
    """Test that get_metrics includes p95_residual_risk."""
    m = Slot6Metrics(window=16)
    for v in [0.1, 0.3, 0.9]:
        m.record_decision("approved", 0.8, v)

    metrics = m.get_metrics()
    assert "p95_residual_risk" in metrics
    assert 0.1 <= metrics["p95_residual_risk"] <= 0.9


def test_thread_safety_basic():
    """Basic thread safety test."""
    m = Slot6Metrics(window=32)

    def worker():
        for i in range(10):
            m.record_decision("test", 0.8, i / 10.0)

    threads = [threading.Thread(target=worker) for _ in range(3)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    # Should have some data and p95 should be calculable
    p95 = m.p95_residual_risk()
    assert p95 is not None
    assert 0.0 <= p95 <= 1.0
