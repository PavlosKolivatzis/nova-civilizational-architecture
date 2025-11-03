import time

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

    now = time.time()

    def fake_peer_metrics(timeout=None):
        peers = [Peer("node-a"), Peer("node-b")]
        checkpoint = {"height": 42}
        stats = {
            "node-a": {"duration": 0.1, "success": True, "last_success_ts": now},
            "node-b": {"duration": 0.2, "success": True, "last_success_ts": now},
        }
        return peers, checkpoint, stats

    monkeypatch.setattr(poller, "get_peer_metrics", fake_peer_metrics)

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
    poller.reset_peer_quality_state()
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
    peer_last_seen = metrics["peer_last_seen"]
    assert peer_last_seen.labels(peer="node-a")._value.get() > 0
    assert peer_last_seen.labels(peer="node-b")._value.get() > 0
    assert metrics["ready"]._value.get() == 1.0


def test_poller_marks_not_ready_on_error(monkeypatch):
    from orchestrator import federation_poller as poller

    metrics = m()

    def raise_error(timeout=None):
        raise RuntimeError("boom")

    poller.reset_peer_quality_state()
    monkeypatch.setattr(poller, "get_peer_metrics", raise_error)

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
    fake_event.clear()

    poller._loop()

    assert metrics["ready"]._value.get() == 0.0
    last_error = metrics["last_result_ts"].labels(status="error")._value.get()
    assert last_error > 0


def test_poller_not_ready_when_no_peers(monkeypatch):
    from orchestrator import federation_poller as poller

    metrics = m()
    metrics["ready"].set(1.0)

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
    poller.reset_peer_quality_state()
    poller._known_peers = {"node-a"}
    metrics["peer_last_seen"].labels(peer="node-a").set(123.0)
    def fake_peer_metrics(timeout=None):
        return [], {"height": 12}, {}

    monkeypatch.setattr(poller, "get_peer_metrics", fake_peer_metrics)
    fake_event.clear()

    poller._loop()

    assert metrics["ready"]._value.get() == 0.0
    assert metrics["peers"]._value.get() == 0
    assert metrics["peer_last_seen"].labels(peer="node-a")._value.get() == 0.0
