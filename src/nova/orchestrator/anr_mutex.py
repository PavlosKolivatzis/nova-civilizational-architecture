"""
ANR Bandit State Mutex Wrapper
Cross-platform file lock + atomic JSON write helpers.
- Windows: msvcrt.locking
- Unix:    fcntl.flock
"""

from __future__ import annotations
import json
import os
import time
import tempfile
from contextlib import contextmanager
from typing import Any, Dict, Optional

# --- platform-specific imports ---
_IS_WIN = os.name == "nt"
if _IS_WIN:
    import msvcrt
else:  # posix
    import fcntl

# -------- File lock --------

@contextmanager
def file_lock(lock_path: str, timeout: float = 10.0, poll_interval: float = 0.05):
    """
    Exclusive lock using a companion .lock file.
    - lock_path: path to the lock file (e.g., "<state>.lock")
    - timeout:   seconds to wait before raising TimeoutError
    """
    # Ensure directory exists
    os.makedirs(os.path.dirname(os.path.abspath(lock_path)), exist_ok=True)

    # Open/ create the lock file in append mode (shared path safe)
    f = open(lock_path, "a+b")
    start = time.time()

    try:
        if _IS_WIN:
            # Lock 1 byte at start of file (non-blocking retry loop)
            while True:
                try:
                    msvcrt.locking(f.fileno(), msvcrt.LK_NBLCK, 1)
                    break
                except OSError:
                    if (time.time() - start) >= timeout:
                        raise TimeoutError(f"Timeout acquiring lock: {lock_path}")
                    time.sleep(poll_interval)
        else:
            # BLOCK with timeout using polling (fcntl has no native timeout)
            while True:
                try:
                    fcntl.flock(f.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                    break
                except OSError:
                    if (time.time() - start) >= timeout:
                        raise TimeoutError(f"Timeout acquiring lock: {lock_path}")
                    time.sleep(poll_interval)

        # We hold the lock
        yield
    finally:
        # Best-effort unlock + close
        try:
            if _IS_WIN:
                try:
                    msvcrt.locking(f.fileno(), msvcrt.LK_UNLCK, 1)
                except OSError:
                    pass
            else:
                try:
                    fcntl.flock(f.fileno(), fcntl.LOCK_UN)
                except OSError:
                    pass
        finally:
            f.close()

# -------- Atomic write helpers --------

def _fsync_dir(path: str) -> None:
    """Ensure directory entry is durable."""
    try:
        dfd = os.open(os.path.dirname(os.path.abspath(path)) or ".", os.O_RDONLY)
        try:
            os.fsync(dfd)
        finally:
            os.close(dfd)
    except (OSError, AttributeError):
        # Windows doesn't support directory fsync in all cases
        pass

def write_atomic_bytes(target_path: str, data: bytes) -> None:
    """
    Write bytes atomically:
      - write to temp file in same dir
      - fsync temp
      - os.replace to target (atomic on same filesystem)
      - fsync directory entry
    """
    dirpath = os.path.dirname(os.path.abspath(target_path)) or "."
    os.makedirs(dirpath, exist_ok=True)

    fd, tmp_path = tempfile.mkstemp(prefix=".tmp-", dir=dirpath)
    try:
        with os.fdopen(fd, "wb", buffering=0) as tmp:
            tmp.write(data)
            tmp.flush()
            os.fsync(tmp.fileno())
        os.replace(tmp_path, target_path)  # atomic rename
        _fsync_dir(target_path)
    finally:
        try:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
        except OSError:
            pass

def save_json_atomic(path: str, obj) -> None:
    """UTF-8, LF newlines, stable keys for deterministic diffs."""
    data = json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    write_atomic_bytes(path, data)

# -------- Legacy compatibility API --------

class ANRStateMutex:
    """Legacy wrapper for backward compatibility."""

    def __init__(self, state_path: str, lock_timeout: int = 30):
        self.state_path = state_path
        self.lock_path = f"{state_path}.lock"
        self.lock_timeout = float(lock_timeout)

    @contextmanager
    def acquire(self):
        """Acquire exclusive lock for state file operations."""
        with file_lock(self.lock_path, timeout=self.lock_timeout):
            yield

    def read_state(self) -> Optional[Dict[str, Any]]:
        """Read bandit state with mutex protection."""
        with self.acquire():
            if not os.path.exists(self.state_path):
                return None
            try:
                with open(self.state_path, 'rb') as f:
                    data = f.read()
                return json.loads(data.decode('utf-8'))
            except (json.JSONDecodeError, IOError, UnicodeDecodeError):
                return None

    def write_state(self, state: Dict[str, Any]) -> bool:
        """Write bandit state with mutex protection and atomic operation."""
        try:
            with self.acquire():
                save_json_atomic(self.state_path, state)
            return True
        except Exception:
            return False

# Global mutex instance (initialized on first use)
_mutex_instance = None

def get_anr_mutex(state_path: str) -> ANRStateMutex:
    """Get global ANR state mutex instance."""
    global _mutex_instance
    if _mutex_instance is None or _mutex_instance.state_path != state_path:
        _mutex_instance = ANRStateMutex(state_path)
    return _mutex_instance

# Convenience functions for common operations
def safe_read_anr_state(state_path: str) -> Optional[Dict[str, Any]]:
    """Safely read ANR bandit state with mutex protection."""
    return get_anr_mutex(state_path).read_state()

def safe_write_anr_state(state_path: str, state: Dict[str, Any]) -> bool:
    """Safely write ANR bandit state with mutex protection."""
    return get_anr_mutex(state_path).write_state(state)
