import time

import pytest

from nova.federation.metrics import m


class DummyPoller:
    def __init__(self, base_interval: float = 5.0):
        self._interval = base_interval
        self.base_interval = base_interval
        self.stopped = 0
        self.started = 0

    def get_interval(self) -> float:
        return self._interval

    def get_base_interval(self) -> float:
        return self.base_interval

    def set_interval(self, seconds: float) -> float:
        self._interval = seconds
        return self._interval

    def stop(self) -> None:
        self.stopped += 1

    def start(self) -> None:
        self.started += 1


@pytest.fixture(autouse=True)
def _reset_metrics():
    metrics = m()
    metrics["ready"].set(1.0)
    metrics["peer_last_seen"].labels(peer="dummy").set(0.0)
    yield


def test_remediator_triggers_on_error_rate(monkeypatch):
    from orchestrator.federation_remediator import FederationRemediator

    metrics = m()
    dummy = DummyPoller()
    remediator = FederationRemediator(
        dummy,
        max_errors=1,
        error_ratio_threshold=0.0,
        ready_failures=10,
        cooldown_seconds=0.0,
        check_period=0.05,
        restart_sleep=0.01,
        max_backoff=dummy.base_interval * 4,
    )

    success_counter = metrics["pull_result"].labels(status="success")
    error_counter = metrics["pull_result"].labels(status="error")

    remediator.start()
    # ensure baseline observation
    time.sleep(0.06)

    error_counter.inc()
    time.sleep(0.2)
    remediator.stop()

    assert dummy.stopped >= 1
    assert dummy.started >= 1
    events = metrics["remediation_events"].labels(reason="error_spike")._value.get()
    assert events >= 1


def test_remediator_triggers_on_readiness_drop():
    from orchestrator.federation_remediator import FederationRemediator

    metrics = m()
    dummy = DummyPoller()
    remediator = FederationRemediator(
        dummy,
        max_errors=5,
        ready_failures=2,
        cooldown_seconds=0.0,
        check_period=0.05,
        restart_sleep=0.01,
        max_backoff=dummy.base_interval * 2,
    )

    remediator.start()
    metrics["ready"].set(0.0)
    # Allow enough evaluation cycles for readiness failure detection even when
    # configuration warnings (e.g., zero peers) add slight latency.
    time.sleep(0.2)
    remediator.stop()

    assert metrics["remediation_events"].labels(reason="readiness_zero")._value.get() >= 1
