import pytest

from slots.slot08_memory_ethics.lock_guard import (
    MemoryLock,
    EthicsGuard,
    MemoryTamperError,
)


def reset_registry():
    EthicsGuard._registry.clear()


def test_memory_lock_basic():
    lock = MemoryLock.create({"a": 1, "b": 2})
    assert lock.verify() is True
    assert lock.read() == {"a": 1, "b": 2}


def test_memory_lock_tampering():
    lock = MemoryLock.create([1, 2, 3])
    lock.data.append(4)  # direct tamper
    assert lock.verify() is False
    with pytest.raises(MemoryTamperError):
        lock.read()


def test_memory_lock_read_only():
    lock = MemoryLock.create({"v": 1}, read_only=True)
    with pytest.raises(MemoryTamperError):
        lock.write({"v": 2})
    data = lock.read(detach=True)
    assert data == {"v": 1}
    assert data is not lock.data


def test_ethics_guard_access_control():
    reset_registry()
    EthicsGuard.register(
        "alpha",
        {"x": 1},
        readers={"alice"},
        writers={"bob"},
        actor="admin",
    )
    assert EthicsGuard.read("alpha", "alice") == {"x": 1}
    with pytest.raises(PermissionError):
        EthicsGuard.read("alpha", "mallory")
    with pytest.raises(PermissionError):
        EthicsGuard.write("alpha", "mallory", {"x": 2})
    EthicsGuard.write("alpha", "bob", {"x": 2})
    assert EthicsGuard.read("alpha", "alice") == {"x": 2}


def test_ethics_guard_policy_update():
    reset_registry()
    EthicsGuard.register(
        "beta", 1, readers={"alice"}, writers={"alice"}, actor="root"
    )
    with pytest.raises(PermissionError):
        EthicsGuard.read("beta", "eve")
    EthicsGuard.update_policies("beta", "root", readers={"alice", "eve"})
    assert EthicsGuard.read("beta", "eve") == 1

