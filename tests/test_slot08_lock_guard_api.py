import pytest

from slots.slot08_memory_ethics.lock_guard import MemoryLock, EthicsGuard


def test_memory_lock_basic():
    lock = MemoryLock("my_var", {"a": 1, "b": 2})
    assert lock.name == "my_var"
    assert lock.get() == {"a": 1, "b": 2}
    assert lock.verify_integrity() is True


def test_memory_lock_tampering():
    lock = MemoryLock("my_var", [1, 2, 3])
    lock._data.append(4)  # Tamper the data intentionally
    assert lock.verify_integrity() is False


def test_memory_lock_reset_and_hash_change():
    lock = MemoryLock("counter", 1)
    old_hash = lock._hash
    lock.set(2)
    new_hash = lock._hash
    assert old_hash != new_hash
    assert lock.verify_integrity() is True


def test_ethics_guard_register_and_validate():
    EthicsGuard.reset()
    m1 = MemoryLock("alpha", "safe")
    m2 = MemoryLock("beta", 42)
    EthicsGuard.register(m1)
    EthicsGuard.register(m2)
    assert EthicsGuard.validate_all() is True


def test_ethics_guard_detect_violation():
    EthicsGuard.reset()
    m1 = MemoryLock("x", [1, 2])
    EthicsGuard.register(m1)
    m1._data.append(3)  # corrupt
    result = EthicsGuard.validate_all()
    assert result is False
    audit = EthicsGuard.get_audit_report()
    assert any(e["valid"] is False for e in audit)
    assert audit[0]["slot"] == "slot08"


def test_ethics_guard_audit_report_structure():
    EthicsGuard.reset()
    m = MemoryLock("trace", {"z": 9})
    EthicsGuard.register(m)
    audit = EthicsGuard.get_audit_report()
    assert isinstance(audit, list)
    assert "name" in audit[0]
    assert "hash" in audit[0]
    assert "valid" in audit[0]
    assert "slot" in audit[0]

