import pytest

from nova.federation.metrics import m


def test_remediation_metrics_exist_and_increment():
    metrics = m()
    counter = metrics["remediation_events"].labels(reason="unit_test")
    baseline = counter._value.get()
    counter.inc()
    assert counter._value.get() == pytest.approx(baseline + 1)

    gauge = metrics["remediation_backoff"]
    gauge.set(42.0)
    assert gauge._value.get() == pytest.approx(42.0)

    timestamp_gauge = metrics["remediation_last_action"]
    timestamp_gauge.set(123.0)
    assert timestamp_gauge._value.get() == pytest.approx(123.0)

    info = metrics["remediation_last_event"]
    info.info({"reason": "unit_test", "interval": "5", "timestamp": "123"})
