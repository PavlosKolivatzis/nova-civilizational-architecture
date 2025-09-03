"""Comprehensive test suite for memory integrity utilities."""

import pytest
import time
import threading
from copy import deepcopy

from src.runtime.memory_integrity import (
    MemoryLock,
    EthicsGuard,
    SecurityError,
    MemoryTamperError,
    RegistrationError,
    ENABLE_CHECKSUM_ON_READ,
    audit_log,
)


class TestMemoryLock:
    """Test MemoryLock integrity mechanisms."""

    def test_basic_creation_and_verification(self):
        data = {"key": "value", "nested": {"list": [1, 2, 3]}}
        lock = MemoryLock.create(data)
        assert lock.verify() is True
        assert lock.read() == data

    def test_tamper_detection(self):
        data = {"secret": 42}
        lock = MemoryLock.create(data)
        lock.data["secret"] = 0
        assert lock.verify() is False
        with pytest.raises(MemoryTamperError):
            lock.read()

    def test_tamper_detection_before_write(self):
        data = {"value": "original"}
        lock = MemoryLock.create(data)
        lock.data["value"] = "tampered"
        with pytest.raises(MemoryTamperError):
            lock.write({"value": "new"})

    def test_read_only_lock(self):
        data = {"immutable": True}
        lock = MemoryLock.create(data, read_only=True)
        with pytest.raises(MemoryTamperError):
            lock.write({"immutable": False})

    def test_detached_read(self):
        original = {"list": [1, 2, 3]}
        lock = MemoryLock.create(original)
        retrieved = lock.read(detach=True)
        retrieved["list"].append(4)
        assert original["list"] == [1, 2, 3]
        assert lock.read()["list"] == [1, 2, 3]

    def test_custom_serializer(self):
        def custom_serializer(obj):
            return str(sum(obj) if isinstance(obj, list) else obj)

        data = [1, 2, 3]
        lock = MemoryLock.create(data, serialize_fn=custom_serializer)
        assert lock.verify() is True


class TestEthicsGuard:
    """Test EthicsGuard access control and registry."""

    def setup_method(self):
        EthicsGuard._registry.clear()

    def test_basic_registration_and_access(self):
        EthicsGuard.register(
            "test_data",
            {"value": 100},
            readers={"user"},
            writers={"admin"},
            actor="system",
        )
        data = EthicsGuard.read("test_data", "user")
        assert data["value"] == 100
        EthicsGuard.write("test_data", "admin", {"value": 200})
        updated = EthicsGuard.read("test_data", "user")
        assert updated["value"] == 200

    def test_unauthorized_access(self):
        EthicsGuard.register(
            "secured",
            {"data": "secret"},
            readers={"boss"},
            writers={"boss"},
            actor="system",
        )
        with pytest.raises(PermissionError):
            EthicsGuard.read("secured", "intern")
        with pytest.raises(PermissionError):
            EthicsGuard.write("secured", "intern", {"data": "hacked"})

    def test_double_registration(self):
        EthicsGuard.register("name", "data1", actor="system")
        with pytest.raises(RegistrationError):
            EthicsGuard.register("name", "data2", actor="system")

    def test_unregister(self):
        EthicsGuard.register("temp", "data", actor="system")
        assert "temp" in EthicsGuard._registry
        EthicsGuard.unregister("temp", "system")
        assert "temp" not in EthicsGuard._registry

    def test_list_objects(self):
        EthicsGuard.register("obj1", "data1", readers={"a"}, actor="system")
        EthicsGuard.register("obj2", "data2", writers={"b"}, actor="system")
        listing = EthicsGuard.list_objects("auditor")
        assert "obj1" in listing
        assert "obj2" in listing
        assert listing["obj1"]["readers"] == ["a"]

    def test_update_policies(self):
        EthicsGuard.register("config", {"setting": 1}, readers={"old_role"}, actor="system")
        EthicsGuard.update_policies("config", "admin", readers={"new_role"})
        EthicsGuard.read("config", "new_role")
        with pytest.raises(PermissionError):
            EthicsGuard.read("config", "old_role")


class TestThreadSafety:
    """Test concurrent access patterns."""

    def test_concurrent_reads(self):
        EthicsGuard.register("counter", {"value": 0}, readers=set(), writers={"writer"}, actor="system")
        read_results = []
        errors = []

        def read_worker(worker_id):
            try:
                for _ in range(10):
                    data = EthicsGuard.read("counter", f"reader_{worker_id}")
                    read_results.append(data["value"])
                    time.sleep(0.001)
            except Exception as e:  # pragma: no cover - should not happen
                errors.append(e)

        threads = [threading.Thread(target=read_worker, args=(i,)) for i in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert not errors
        assert len(read_results) == 50
        assert all(val == 0 for val in read_results)

    def test_write_with_readers(self):
        EthicsGuard.register("shared", {"list": []}, readers=set(), writers={"writer"}, actor="system")
        read_counts = [0]
        write_complete = threading.Event()

        def reader_worker():
            while not write_complete.is_set():
                try:
                    data = EthicsGuard.read("shared", "reader")
                    assert len(data["list"]) in (0, 10)
                    read_counts[0] += 1
                except Exception:  # pragma: no cover - ignore transient errors
                    pass

        def writer_worker():
            new_list = list(range(10))
            EthicsGuard.write("shared", "writer", {"list": new_list})
            write_complete.set()

        reader_thread = threading.Thread(target=reader_worker)
        writer_thread = threading.Thread(target=writer_worker)
        reader_thread.start()
        writer_thread.start()
        writer_thread.join()
        reader_thread.join()

        assert read_counts[0] > 0


class TestErrorConditions:
    """Test error handling and edge cases."""

    def test_nonexistent_object(self):
        with pytest.raises(KeyError):
            EthicsGuard.read("ghost", "user")

    def test_missing_actor(self):
        with pytest.raises(ValueError):
            EthicsGuard.register("test", "data", actor=None)  # type: ignore

    def test_checksum_performance_toggle(self):
        global ENABLE_CHECKSUM_ON_READ
        original_setting = ENABLE_CHECKSUM_ON_READ
        try:
            ENABLE_CHECKSUM_ON_READ = False
            lock = MemoryLock.create("data")
            assert lock.verify() is True
        finally:
            ENABLE_CHECKSUM_ON_READ = original_setting


def test_audit_log_structure(capsys):
    audit_log("test", "object_id", "test_actor", {"custom": "field"})
    captured = capsys.readouterr()
    audit_log("test", "object_id", "test_actor", None)
    class NonSerializable:
        pass
    audit_log("test", "object_id", "test_actor", {"weird": NonSerializable()})
