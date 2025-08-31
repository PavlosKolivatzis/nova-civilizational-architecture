import pytest

from orchestrator.recovery import trigger_recovery


class Protocol:
    def __init__(self, locks, required):
        self.locks = locks
        self.required_locks = required


def ok_verify(domain, anchor):
    return anchor == "ok"


def test_trigger_recovery_success():
    protocol = Protocol({"d1": "ok", "d2": "ok"}, ["d1", "d2"])
    assert trigger_recovery(protocol, ok_verify) is True


def test_trigger_recovery_failure_missing_lock():
    protocol = Protocol({"d1": "ok"}, ["d1", "d2"])
    with pytest.raises(RuntimeError) as exc:
        trigger_recovery(protocol, ok_verify)
    assert "d2" in str(exc.value)


def test_trigger_recovery_failure_verification():
    protocol = Protocol({"d1": "bad"}, ["d1"])
    with pytest.raises(RuntimeError) as exc:
        trigger_recovery(protocol, ok_verify)
    assert "d1" in str(exc.value)
