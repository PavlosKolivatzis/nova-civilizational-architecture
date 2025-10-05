import json
import threading
import time
from pathlib import Path
from tempfile import TemporaryDirectory

import pytest

from orchestrator import anr_mutex


def test_file_lock_allows_single_holder_and_releases():
    with TemporaryDirectory() as tmp:
        lock_path = str(Path(tmp) / "state.lock")
        # Acquire and release without error
        with anr_mutex.file_lock(lock_path, timeout=0.5):
            assert Path(lock_path).exists()
        # Lock can be acquired again after release
        with anr_mutex.file_lock(lock_path, timeout=0.5):
            assert Path(lock_path).exists()


def test_file_lock_timeout_when_already_held():
    with TemporaryDirectory() as tmp:
        lock_path = str(Path(tmp) / "state.lock")
        hold_event = threading.Event()
        release_event = threading.Event()

        def holder():
            with anr_mutex.file_lock(lock_path, timeout=1):
                hold_event.set()
                release_event.wait()

        thread = threading.Thread(target=holder)
        thread.start()
        assert hold_event.wait(1), "Lock holder did not start in time"
        try:
            with pytest.raises(TimeoutError):
                with anr_mutex.file_lock(lock_path, timeout=0.2, poll_interval=0.05):
                    pass  # pragma: no cover (never reached)
        finally:
            release_event.set()
            thread.join()


def test_save_and_read_state_round_trip():
    with TemporaryDirectory() as tmp:
        state_path = Path(tmp) / "bandit_state.json"
        state = {"weights": [0.1, 0.2, 0.3], "timestamp": 123456}

        assert anr_mutex.safe_write_anr_state(str(state_path), state)
        loaded = anr_mutex.safe_read_anr_state(str(state_path))
        assert loaded == state


def test_read_state_invalid_json_returns_none():
    with TemporaryDirectory() as tmp:
        state_path = Path(tmp) / "bandit_state.json"
        state_path.write_text("not-json")
        assert anr_mutex.safe_read_anr_state(str(state_path)) is None


def test_write_atomic_bytes_replaces_existing_file():
    with TemporaryDirectory() as tmp:
        target = Path(tmp) / "payload.bin"
        target.write_bytes(b"old")
        anr_mutex.write_atomic_bytes(str(target), b"new-bytes")
        assert target.read_bytes() == b"new-bytes"


def test_save_json_atomic_serializes_sorted_keys():
    with TemporaryDirectory() as tmp:
        target = Path(tmp) / "data.json"
        payload = {"b": 1, "a": 2}
        anr_mutex.save_json_atomic(str(target), payload)
        raw = target.read_text("utf-8")
        # keys should be sorted and compact separators applied
        assert raw == json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def test_get_anr_mutex_returns_cached_instance():
    with TemporaryDirectory() as tmp:
        state_path = str(Path(tmp) / "state.json")
        first = anr_mutex.get_anr_mutex(state_path)
        second = anr_mutex.get_anr_mutex(state_path)
        assert first is second
        other_path = str(Path(tmp) / "other.json")
        third = anr_mutex.get_anr_mutex(other_path)
        assert third is not first
