"""Memory integrity utilities with ethical access enforcement.

This module provides simple primitives to guard in-memory objects against
tampering while keeping a lightweight audit trail.  It exposes a
``MemoryLock`` wrapper that maintains a checksum of the protected object and an
``EthicsGuard`` registry that can validate multiple locks and report their
status.
"""

from __future__ import annotations

import hashlib
import json
import secrets
import time
from typing import Any, Dict, List, Optional

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

class MemoryLock:
    """Wrap an object with checksum verification and tamper detection.

    The implementation is intentionally lightweight.  Each instance keeps the
    original data and a SHA256 hash of its serialised representation.  The hash
    is recomputed on demand to detect external mutations.
    """

    def __init__(self, name: str, data: Any) -> None:
        self.name = name
        self._data = data
        self._hash = self._compute_hash(data)
        # ``checksum`` mirrors ``_hash`` for backward compatibility with
        # existing integrations within the code base.
        self.checksum = self._hash

    # ------------------------------------------------------------------
    # Construction helpers
    # ------------------------------------------------------------------
    @classmethod
    def create(cls, data: Any, name: Optional[str] = None) -> "MemoryLock":
        """Create a new ``MemoryLock`` computing the checksum for ``data``.

        Parameters
        ----------
        data:
            The object to protect.
        name:
            Optional identifier.  If omitted, a generic name is used.
        """

        return cls(name or "memory", data)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    @staticmethod
    def _compute_hash(data: Any) -> str:
        try:
            serialized = json.dumps(data, sort_keys=True).encode()
        except TypeError:
            serialized = repr(data).encode()
        return hashlib.sha256(serialized).hexdigest()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def verify_integrity(self) -> bool:
        """Return ``True`` if the current data matches the stored checksum."""

        return secrets.compare_digest(self._compute_hash(self._data), self._hash)

    # Alias used elsewhere in the repository
    def verify(self) -> bool:  # pragma: no cover - thin wrapper
        return self.verify_integrity()

    def get(self) -> Any:
        """Return the protected data after integrity validation."""

        if not self.verify_integrity():
            raise ValueError("memory tamper detected")
        return self._data

    def set(self, new_data: Any) -> None:
        """Replace the protected data, updating the checksum."""

        if not self.verify_integrity():
            raise ValueError("memory tamper detected before write")
        self._data = new_data
        self._hash = self._compute_hash(new_data)
        self.checksum = self._hash

    # Backwards compatible helpers -------------------------------------------------
    def read(self) -> Any:  # pragma: no cover - delegates to ``get``
        return self.get()

    def write(self, new_data: Any) -> None:  # pragma: no cover - delegates to ``set``
        self.set(new_data)

    @property
    def data(self) -> Any:  # pragma: no cover - convenience accessor
        return self.get()


# ---------------------------------------------------------------------------
# EthicsGuard registry
# ---------------------------------------------------------------------------

class EthicsGuard:
    """Registry tracking memory locks and providing integrity audits."""

    _locks: Dict[str, MemoryLock] = {}
    _audit: List[Dict[str, Any]] = []

    @classmethod
    def reset(cls) -> None:
        cls._locks = {}
        cls._audit = []

    @classmethod
    def register(cls, lock: MemoryLock) -> None:
        """Register a new lock for auditing."""

        cls._locks[lock.name] = lock
        cls._audit.append(
            {
                "name": lock.name,
                "hash": lock._hash,
                "valid": lock.verify_integrity(),
                "slot": "slot08",
            }
        )

    @classmethod
    def validate_all(cls) -> bool:
        """Recompute integrity for all registered locks.

        Returns ``True`` if every lock is valid, otherwise ``False``.  The audit
        report is refreshed on each invocation.
        """

        cls._audit = []
        all_valid = True
        for lock in cls._locks.values():
            valid = lock.verify_integrity()
            cls._audit.append(
                {
                    "name": lock.name,
                    "hash": lock._hash,
                    "valid": valid,
                    "slot": "slot08",
                }
            )
            all_valid = all_valid and valid
        return all_valid

    @classmethod
    def get_audit_report(cls) -> List[Dict[str, Any]]:
        """Return the most recent audit results."""

        return list(cls._audit)


__all__ = ["MemoryLock", "EthicsGuard", "audit_log"]

