"""Test GovernorState — single source of truth for η."""

import threading
import time

import pytest

from nova.governor import state as module


def setup_function():
    """Reset state before each test."""
    module.reset_for_tests(eta=0.10, frozen=False)


def test_initial_state():
    """Test default initial values."""
    assert module.get_eta() == pytest.approx(0.10)
    assert module.is_frozen() is False
    assert module.get_training_eta() == pytest.approx(0.10)


def test_set_eta():
    """Test setting learning rate."""
    module.set_eta(0.15)
    assert module.get_eta() == pytest.approx(0.15)
    assert module.get_training_eta() == pytest.approx(0.15)


def test_frozen_returns_zero_eta():
    """Test that get_training_eta() returns 0.0 when frozen."""
    module.set_eta(0.12)
    module.set_frozen(True)

    assert module.is_frozen() is True
    assert module.get_eta() == pytest.approx(0.12)  # Raw value preserved
    assert module.get_training_eta() == pytest.approx(0.0)  # Training sees 0


def test_unfrozen_resumes_normal_eta():
    """Test that unfreezing resumes normal eta."""
    module.set_eta(0.12)
    module.set_frozen(True)
    assert module.get_training_eta() == pytest.approx(0.0)

    module.set_frozen(False)
    assert module.get_training_eta() == pytest.approx(0.12)


def test_get_state_atomic():
    """Test atomic state read."""
    module.set_eta(0.14)
    module.set_frozen(True)

    eta, frozen = module.get_state()
    assert eta == pytest.approx(0.14)
    assert frozen is True


def test_reset_for_tests():
    """Test reset functionality."""
    module.set_eta(0.18)
    module.set_frozen(True)

    module.reset_for_tests(eta=0.08, frozen=False)

    assert module.get_eta() == pytest.approx(0.08)
    assert module.is_frozen() is False


def test_thread_safety_concurrent_reads():
    """Test that concurrent reads don't corrupt state."""
    module.set_eta(0.12)

    results = []

    def reader():
        for _ in range(100):
            eta = module.get_eta()
            results.append(eta)
            time.sleep(0.0001)

    threads = [threading.Thread(target=reader) for _ in range(10)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    # All reads should see consistent value
    assert all(r == pytest.approx(0.12) for r in results)


def test_thread_safety_concurrent_writes():
    """Test that concurrent writes don't corrupt state."""

    def writer(value):
        for _ in range(50):
            module.set_eta(value)
            time.sleep(0.0001)

    threads = [
        threading.Thread(target=writer, args=(0.10,)),
        threading.Thread(target=writer, args=(0.15,)),
        threading.Thread(target=writer, args=(0.18,)),
    ]

    for t in threads:
        t.start()
    for t in threads:
        t.join()

    # Final state should be one of the written values (not corrupted)
    final_eta = module.get_eta()
    assert final_eta in {pytest.approx(0.10), pytest.approx(0.15), pytest.approx(0.18)}


def test_thread_safety_read_write_mixed():
    """Test mixed concurrent reads and writes."""
    module.set_eta(0.10)
    read_values = []
    write_complete = threading.Event()

    def reader():
        while not write_complete.is_set():
            read_values.append(module.get_training_eta())
            time.sleep(0.0001)

    def writer():
        for i in range(20):
            module.set_eta(0.10 + i * 0.001)
            time.sleep(0.001)
        write_complete.set()

    reader_threads = [threading.Thread(target=reader) for _ in range(3)]
    writer_thread = threading.Thread(target=writer)

    for t in reader_threads:
        t.start()
    writer_thread.start()

    writer_thread.join()
    for t in reader_threads:
        t.join()

    # All read values should be valid floats (no corruption)
    assert all(isinstance(v, float) for v in read_values)
    assert all(0.0 <= v <= 0.20 for v in read_values)


def test_frozen_state_thread_safe():
    """Test that frozen state changes are thread-safe."""
    module.set_eta(0.12)

    def freezer():
        for _ in range(50):
            module.set_frozen(True)
            time.sleep(0.0001)

    def unfreezer():
        for _ in range(50):
            module.set_frozen(False)
            time.sleep(0.0001)

    threads = [
        threading.Thread(target=freezer),
        threading.Thread(target=unfreezer),
    ]

    for t in threads:
        t.start()
    for t in threads:
        t.join()

    # Final frozen state should be boolean (not corrupted)
    assert isinstance(module.is_frozen(), bool)


def test_public_api():
    """Test that only intended symbols are exported."""
    public = {name for name in dir(module) if not name.startswith("_")}
    expected = {
        "GovernorState",
        "get_eta",
        "get_state",
        "get_training_eta",
        "is_frozen",
        "set_eta",
        "set_frozen",
        "reset_for_tests",
        "MODULE_STATE",
        "__all__",
        "dataclass",
        "threading",
        "Tuple",
    }
    assert public <= expected

    exported = set(module.__all__)
    assert exported == {
        "GovernorState",
        "get_training_eta",
        "get_eta",
        "set_eta",
        "is_frozen",
        "set_frozen",
        "get_state",
        "reset_for_tests",
    }
