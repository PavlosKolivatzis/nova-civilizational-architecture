from types import SimpleNamespace

import pytest

import orchestrator.adapters.slot8_memory_ethics as slot8_adapter


@pytest.fixture
def adapter():
    return slot8_adapter.Slot8MemoryEthicsAdapter()


def test_register_success(monkeypatch, adapter):
    sentinel = SimpleNamespace(lock=True)

    class StubGuard:
        @staticmethod
        def register(name, data, *, readers=None, writers=None, actor=None):
            return sentinel

    monkeypatch.setattr(slot8_adapter, "EthicsGuard", StubGuard)
    adapter.available = True

    result = adapter.register("memory", {"x": 1}, actor="tester")
    assert result is sentinel


def test_register_handles_exception(monkeypatch, adapter):
    class StubGuard:
        @staticmethod
        def register(*args, **kwargs):
            raise RuntimeError("boom")

    monkeypatch.setattr(slot8_adapter, "EthicsGuard", StubGuard)
    adapter.available = True

    assert adapter.register("memory", {"x": 1}, actor="tester") is None


def test_register_returns_none_when_unavailable(adapter):
    adapter.available = False
    assert adapter.register("memory", {"x": 1}, actor="tester") is None


def test_read_success(monkeypatch, adapter):
    sentinel = {"payload": 42}

    class StubGuard:
        @staticmethod
        def read(name, actor):
            return sentinel

    monkeypatch.setattr(slot8_adapter, "EthicsGuard", StubGuard)
    adapter.available = True

    assert adapter.read("memory", "tester") is sentinel


def test_read_handles_exception(monkeypatch, adapter):
    class StubGuard:
        @staticmethod
        def read(*_):
            raise RuntimeError("nope")

    monkeypatch.setattr(slot8_adapter, "EthicsGuard", StubGuard)
    adapter.available = True

    assert adapter.read("memory", "tester") is None


def test_read_returns_none_when_unavailable(adapter):
    adapter.available = False
    assert adapter.read("memory", "tester") is None


def test_write_success(monkeypatch, adapter):
    calls = {}

    class StubGuard:
        @staticmethod
        def write(name, actor, data):
            calls["called"] = (name, actor, data)

    monkeypatch.setattr(slot8_adapter, "EthicsGuard", StubGuard)
    adapter.available = True

    assert adapter.write("memory", "tester", {"value": 1}) is True
    assert calls["called"] == ("memory", "tester", {"value": 1})


def test_write_handles_exception(monkeypatch, adapter):
    class StubGuard:
        @staticmethod
        def write(*_):
            raise RuntimeError("fail")

    monkeypatch.setattr(slot8_adapter, "EthicsGuard", StubGuard)
    adapter.available = True

    assert adapter.write("memory", "tester", {}) is False


def test_write_returns_false_when_unavailable(adapter):
    adapter.available = False
    assert adapter.write("memory", "tester", {}) is False
