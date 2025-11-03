"""Exercise federation auto-remediation trigger logic."""

import time

import pytest

from nova.federation.metrics import m


class DummyPoller:
    def __init__(self, base_interval: float = 5.0) -> None:
        self._interval = base_interval
        self._base = base_interval
        self.start_calls = 0
        self.stop_calls = 0

    def get_interval(self) -> float:
        return self._interval

    def get_base_interval(self) -> float:
        return self._base

    def set_interval(self, seconds: float) -> float:
        self._interval = seconds
        return self._interval

    def start(self) -> None:
        self.start_calls += 1

    def stop(self) -> None:
        self.stop_calls += 1


def test_remediator_triggers_and_restarts_poller():
    from orchestrator.federation_remediator import FederationRemediator

    metrics = m()
    poller = DummyPoller()
    remediator = FederationRemediator(
        poller,
        max_errors=1,
        error_ratio_threshold=0.5,
        ready_failures=10,
        cooldown_seconds=0.0,
        check_period=0.05,
        restart_sleep=0.01,
        max_backoff=poller.get_base_interval() * 4,
    )

    success = metrics["pull_result"].labels(status="success")
    errors = metrics["pull_result"].labels(status="error")
    events_counter = metrics["remediation_events"].labels(reason="error_spike")

    # Seed baseline so delta calculations work
    success._value.set(1.0)  # type: ignore[attr-defined]
    errors._value.set(0.0)  # type: ignore[attr-defined]
    baseline_events = events_counter._value.get()
    remediator.start()
    time.sleep(0.06)

    # Inject more than 50% error rate during check window
    errors.inc(2.0)
    time.sleep(0.2)
    remediator.stop()

    # Ensure hooks ran
    assert poller.stop_calls >= 1, "Poller stop should be invoked"
    assert poller.start_calls >= 1, "Poller start should be invoked"
    assert (
        events_counter._value.get() >= baseline_events + 1
    ), "Remediation counter should increment"
    assert metrics["remediation_backoff"]._value.get() >= poller.get_base_interval()


def test_remediator_logs_config_error_without_restart():
    from orchestrator.federation_remediator import FederationRemediator

    metrics = m()
    poller = DummyPoller()
    remediator = FederationRemediator(
        poller,
        max_errors=5,
        ready_failures=999,
        cooldown_seconds=0.0,
        check_period=0.05,
        restart_sleep=0.01,
        max_backoff=poller.get_base_interval() * 2,
    )

    metrics["peers"].set(0.0)  # simulate misconfiguration with no peers
    counter = metrics["remediation_events"].labels(reason="config_error")
    baseline = counter._value.get()

    remediator.start()
    time.sleep(0.12)
    remediator.stop()

    assert poller.stop_calls == 0, "Config error should not restart poller"
    assert counter._value.get() >= baseline + 1

