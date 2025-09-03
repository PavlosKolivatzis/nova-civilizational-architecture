"""Memory integrity utilities with ethical access enforcement.

This module provides tools to guard in-memory objects against tampering while
maintaining an auditable trail of all read/write operations. It exposes a
:class:`MemoryLock` wrapper that verifies a checksum every time data is read or
written and an :class:`EthicsGuard` registry that applies access policies before
allowing interaction with protected objects.
"""

from __future__ import annotations

import hashlib
import json
import secrets
import time
from dataclasses import dataclass
from typing import Any, Dict, Optional

from .. import memory_logger


# ---------------------------------------------------------------------------
# Audit utilities
# ---------------------------------------------------------------------------

def audit_log(event: str, memory_id: str, actor: Optional[str], extra: Optional[Dict[str, Any]] = None) -> None:
    """Emit a structured audit log entry.

    Parameters
    ----------
    event:
        Human readable event name (e.g. ``"read"`` or ``"write"``).
    memory_id:
        Identifier of the memory object being accessed.
    actor:
        The entity performing the action.
    extra:
        Additional metadata to include in the log for traceability.
    """
    entry: Dict[str, Any] = {
        "event": f"memory_{event}",
        "memory_id": memory_id,
        "actor": actor,
        "timestamp": time.time(),
    }
    if extra:
        entry.update(extra)
    memory_logger.info(json.dumps(entry))


# ---------------------------------------------------------------------------
# MemoryLock
# ---------------------------------------------------------------------------

@dataclass
class MemoryLock:
    """Wrap an object with checksum verification and tamper detection."""

    data: Any
    checksum: str

    @classmethod
    def create(cls, data: Any) -> "MemoryLock":
        """Create a new ``MemoryLock`` computing the checksum for ``data``."""
        return cls(data=data, checksum=cls._checksum(data))

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    @staticmethod
    def _checksum(data: Any) -> str:
        try:
            serialized = json.dumps(data, sort_keys=True).encode()
        except TypeError:
            serialized = repr(data).encode()
        return hashlib.sha256(serialized).hexdigest()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def verify(self) -> bool:
        """Verify the current data matches the stored checksum."""
        expected = self._checksum(self.data)
        return secrets.compare_digest(expected, self.checksum)

    def read(self) -> Any:
        """Return the underlying data after verifying its integrity."""
        if not self.verify():
            raise ValueError("memory tamper detected")
        return self.data

    def write(self, new_data: Any) -> None:
        """Update the data after verifying existing integrity."""
        if not self.verify():
            raise ValueError("memory tamper detected before write")
        self.data = new_data
        self.checksum = self._checksum(new_data)


# ---------------------------------------------------------------------------
# EthicsGuard registry
# ---------------------------------------------------------------------------

class EthicsGuard:
    """Registry tracking memory locks and enforcing ethical access rules."""

    _registry: Dict[str, Dict[str, Any]] = {}

    @classmethod
    def register(
        cls,
        name: str,
        lock: MemoryLock,
        *,
        readers: Optional[set[str]] = None,
        writers: Optional[set[str]] = None,
    ) -> None:
        """Register a memory lock with optional reader/writer policies."""
        cls._registry[name] = {
            "lock": lock,
            "readers": set(readers or []),
            "writers": set(writers or []),
        }

    @classmethod
    def _check_access(cls, name: str, actor: str, action: str) -> MemoryLock:
        if name not in cls._registry:
            raise KeyError(f"memory object '{name}' is not registered")
        record = cls._registry[name]
        allowed = record[f"{action}s"]  # readers or writers
        if allowed and actor not in allowed:
            audit_log("access_denied", name, actor, {"action": action})
            raise PermissionError(f"actor '{actor}' not allowed to {action} '{name}'")
        return record["lock"]

    @classmethod
    def read(cls, name: str, actor: str, metadata: Optional[Dict[str, Any]] = None) -> Any:
        """Read a protected memory object after policy validation."""
        lock = cls._check_access(name, actor, "read")
        data = lock.read()
        audit_log("read", name, actor, {"checksum": lock.checksum, **(metadata or {})})
        return data

    @classmethod
    def write(cls, name: str, actor: str, data: Any, metadata: Optional[Dict[str, Any]] = None) -> None:
        """Write to a protected memory object after policy validation."""
        lock = cls._check_access(name, actor, "write")
        lock.write(data)
        audit_log("write", name, actor, {"checksum": lock.checksum, **(metadata or {})})

