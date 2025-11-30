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


def test_update_empty_peers_triggers_threshold(monkeypatch):
    from nova.orchestrator import federation_poller

    metrics = m()
    counter = metrics["remediation_events"].labels(reason="no_peers")
    error_counter = metrics["pull_result"].labels(status="error")

    baseline_events = counter._value.get()
    baseline_errors = error_counter._value.get()

    monkeypatch.setenv("NOVA_FEDERATION_NO_PEER_THRESHOLD", "2")
    monkeypatch.setenv("NOVA_FEDERATION_NO_PEER_COOLDOWN", "100")
    monkeypatch.setattr(federation_poller, "NO_PEERS_THRESHOLD", 2, raising=False)
    monkeypatch.setattr(federation_poller, "NO_PEERS_COOLDOWN", 100, raising=False)

    federation_poller._EMPTY_PEERS_STREAK = 0
    federation_poller._LAST_EMPTY_PEERS_SIGNAL = 0.0

    federation_poller._update_empty_peers([], metrics)
    assert counter._value.get() == pytest.approx(baseline_events)

    federation_poller._update_empty_peers([], metrics)
    assert counter._value.get() == pytest.approx(baseline_events + 1)
    assert error_counter._value.get() == pytest.approx(baseline_errors + 1)

    federation_poller._update_empty_peers([], metrics)
    assert counter._value.get() == pytest.approx(baseline_events + 1)
    assert error_counter._value.get() == pytest.approx(baseline_errors + 1)


def test_federation_force_errors_flag(monkeypatch):
    from nova.orchestrator import federation_client

    monkeypatch.setenv("NOVA_FED_FORCE_ERRORS", "1")

    with pytest.raises(RuntimeError, match="dev-forced federation failure"):
        federation_client.get_peer_list()

    with pytest.raises(RuntimeError, match="dev-forced federation failure"):
        federation_client.get_verified_checkpoint()
