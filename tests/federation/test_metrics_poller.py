import pytest

from nova.federation.metrics import m


def test_metrics_singleton_cache():
    first = m()
    second = m()
    assert first is second
    first["peers"].set(3)
    assert second["peers"]._value.get() == 3


def test_poller_loop_updates_metrics(monkeypatch):
    from orchestrator import federation_poller as poller

    metrics = m()
    metrics["peers"].set(0)
    metrics["height"].set(0)
    success_counter = metrics["pull_result"].labels(status="success")
    error_counter = metrics["pull_result"].labels(status="error")
    initial_success = success_counter._value.get()
    initial_errors = error_counter._value.get()

    class Peer:
        def __init__(self, id_):
            self.id = id_

    monkeypatch.setattr(poller, "get_peer_list", lambda timeout=None: [Peer("node-a"), Peer("node-b")])
    monkeypatch.setattr(poller, "get_verified_checkpoint", lambda timeout=None: {"height": 42})

    class _FakeEvent:
        def __init__(self):
            self._flag = False

        def is_set(self) -> bool:
            return self._flag

        def set(self) -> None:
            self._flag = True

        def clear(self) -> None:
            self._flag = False

        def wait(self, interval: float) -> bool:
            self._flag = True
            return True

    fake_event = _FakeEvent()
    monkeypatch.setattr(poller, "_stop", fake_event, raising=False)
    poller._known_peers.clear()
    fake_event.clear()

    poller._loop()

    assert metrics["peers"]._value.get() == 2
    assert metrics["height"]._value.get() == 42
    last_success = metrics["last_result_ts"].labels(status="success")._value.get()
    assert last_success > 0
    last_error = metrics["last_result_ts"].labels(status="error")._value.get()
    assert last_error == 0
    assert success_counter._value.get() == pytest.approx(initial_success + 1)
    assert error_counter._value.get() == pytest.approx(initial_errors)
    peer_up = metrics["peer_up"]
    assert peer_up.labels(peer="node-a")._value.get() == 1.0
    assert peer_up.labels(peer="node-b")._value.get() == 1.0
