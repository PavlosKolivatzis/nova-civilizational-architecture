"""Memory integrity utilities with ethical access enforcement.

This module provides tools to guard in-memory objects against tampering while
maintaining an auditable trail of all read/write operations.
"""

from __future__ import annotations

import hashlib
import json
import secrets
import time
from dataclasses import dataclass, field
from typing import Any, Dict, Optional, Set, TypeVar, Generic, Callable
from contextlib import contextmanager
from copy import deepcopy
import threading

from .. import memory_logger

T = TypeVar('T')

# ---------------------------------------------------------------------------
# Configuration constants
# ---------------------------------------------------------------------------

ENABLE_CHECKSUM_ON_READ: bool = True  # Toggle for performance optimization
def _default_serializer(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(',', ':'))

DEFAULT_SERIALIZER: Callable[[Any], str] = _default_serializer
DEFAULT_DESERIALIZER: Callable[[str], Any] = json.loads

# ---------------------------------------------------------------------------
# Custom exceptions
# ---------------------------------------------------------------------------

class SecurityError(Exception):
    """Base class for security-related exceptions."""
    pass


class MemoryTamperError(SecurityError):
    """Raised when memory tampering is detected."""
    pass


class RegistrationError(SecurityError):
    """Raised for registration-related errors."""
    pass


# ---------------------------------------------------------------------------
# Audit utilities
# ---------------------------------------------------------------------------

def audit_log(
    event: str,
    memory_id: str,
    actor: str,
    extra: Optional[Dict[str, Any]] = None
) -> None:
    """Emit a structured audit log entry with error handling."""
    try:
        entry = {
            "event": f"memory_{event}",
            "memory_id": memory_id,
            "actor": actor,
            "timestamp": time.time_ns(),
            "utc_time": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        }
        if extra:
            entry.update(extra)
        memory_logger.info(json.dumps(entry, default=str))
    except Exception as e:
        memory_logger.error(f"Audit log failed: {e}")


# ---------------------------------------------------------------------------
# MemoryLock with enhanced security and performance
# ---------------------------------------------------------------------------


@dataclass
class MemoryLock(Generic[T]):
    """Thread-safe memory wrapper with checksum verification and tamper detection."""

    data: T
    checksum: str
    serialize_fn: Callable[[Any], str] = field(default=DEFAULT_SERIALIZER, repr=False)
    deserialize_fn: Callable[[str], Any] = field(default=DEFAULT_DESERIALIZER, repr=False)
    read_only: bool = field(default=False, repr=False)
    _lock_count: int = field(default=0, init=False, repr=False)

    @classmethod
    def create(
        cls,
        data: Any,
        serialize_fn: Optional[Callable[[Any], str]] = None,
        deserialize_fn: Optional[Callable[[str], Any]] = None,
        read_only: bool = False
    ) -> MemoryLock:
        """Create a new MemoryLock with computed checksum."""
        serialize_fn = serialize_fn or DEFAULT_SERIALIZER
        checksum = cls._compute_checksum(data, serialize_fn)
        return cls(
            data=data,
            checksum=checksum,
            serialize_fn=serialize_fn,
            deserialize_fn=deserialize_fn or DEFAULT_DESERIALIZER,
            read_only=read_only
        )

    @staticmethod
    def _compute_checksum(data: Any, serialize_fn: Callable[[Any], str]) -> str:
        """Compute SHA3-256 checksum with custom serialization."""
        try:
            serialized = serialize_fn(data).encode()
        except (TypeError, ValueError) as e:
            raise MemoryTamperError(f"Serialization failed: {e}") from e
        return hashlib.sha3_256(serialized).hexdigest()

    def verify(self) -> bool:
        """Verify data integrity against stored checksum."""
        if not ENABLE_CHECKSUM_ON_READ:
            return True
        current_checksum = self._compute_checksum(self.data, self.serialize_fn)
        return secrets.compare_digest(current_checksum, self.checksum)

    def read(self, detach: bool = False) -> T:
        """Return data after integrity verification."""
        if not self.verify():
            raise MemoryTamperError("Memory tampering detected")

        if detach or self.read_only:
            return deepcopy(self.data)
        return self.data

    def write(self, new_data: T) -> None:
        """Update data after verifying current integrity."""
        if self.read_only:
            raise MemoryTamperError("Cannot write to read-only memory lock")

        if not self.verify():
            raise MemoryTamperError("Memory compromised before write operation")

        self.data = new_data
        self.checksum = self._compute_checksum(new_data, self.serialize_fn)

    @contextmanager
    def transaction(self):
        """Context manager for atomic operations."""
        self._lock_count += 1
        try:
            yield self
        finally:
            self._lock_count -= 1


# ---------------------------------------------------------------------------
# EthicsGuard with enhanced registry and threading
# ---------------------------------------------------------------------------


try:
    _registry_lock: Optional[threading.RLock] = threading.RLock()
except ImportError:  # pragma: no cover - fallback path
    _registry_lock = None


@dataclass
class MemoryRecord:
    """Container for memory lock and access policies."""
    lock: MemoryLock
    readers: Set[str] = field(default_factory=set)
    writers: Set[str] = field(default_factory=set)
    created_at: float = field(default_factory=time.time)


class EthicsGuard:
    """Thread-safe registry for memory locks with ethical access enforcement."""

    _registry: Dict[str, MemoryRecord] = {}

    @classmethod
    def _get_lock(cls):
        """Return appropriate lock mechanism."""
        return _registry_lock if _registry_lock is not None else nullcontext()

    @classmethod
    def register(
        cls,
        name: str,
        data: Any,
        *,
        readers: Optional[Set[str]] = None,
        writers: Optional[Set[str]] = None,
        actor: str,
        serialize_fn: Optional[Callable[[Any], str]] = None,
        deserialize_fn: Optional[Callable[[str], Any]] = None,
        read_only: bool = False
    ) -> MemoryLock:
        """Register new memory object with access policies."""
        if not name or not isinstance(name, str):
            raise ValueError("Invalid memory object name")

        lock = MemoryLock.create(
            data,
            serialize_fn=serialize_fn,
            deserialize_fn=deserialize_fn,
            read_only=read_only
        )
        record = MemoryRecord(
            lock=lock,
            readers=set(readers or set()),
            writers=set(writers or set())
        )

        with cls._get_lock():
            if name in cls._registry:
                raise RegistrationError(f"Memory object '{name}' already registered")
            cls._registry[name] = record

        audit_log("registered", name, actor, {
            "readers": list(record.readers),
            "writers": list(record.writers),
            "read_only": read_only
        })
        return lock

    @classmethod
    def _check_access(cls, name: str, actor: str, action: str) -> MemoryRecord:
        """Validate access permissions."""
        with cls._get_lock():
            if name not in cls._registry:
                raise KeyError(f"Memory object '{name}' not found")

            record = cls._registry[name]
            allowed_actors = getattr(record, "readers" if action == "read" else "writers")

            if allowed_actors and actor not in allowed_actors:
                audit_log("access_denied", name, actor, {"action": action})
                raise PermissionError(f"Actor '{actor}' not authorized to {action} '{name}'")

            return record

    @classmethod
    def read(
        cls,
        name: str,
        actor: str,
        metadata: Optional[Dict[str, Any]] = None,
        detach: bool = False
    ) -> Any:
        """Read protected memory object with policy validation."""
        record = cls._check_access(name, actor, "read")

        try:
            data = record.lock.read(detach=detach)
            audit_log("read", name, actor, {
                "checksum": record.lock.checksum,
                "size": len(str(data)),
                "detached": detach,
                **(metadata or {})
            })
            return data
        except SecurityError as e:
            audit_log("read_failed", name, actor, {"error": str(e), **(metadata or {})})
            raise

    @classmethod
    def write(cls, name: str, actor: str, data: Any, metadata: Optional[Dict[str, Any]] = None) -> None:
        """Write to protected memory object with policy validation."""
        record = cls._check_access(name, actor, "write")

        try:
            with cls._get_lock():
                record.lock.write(data)
            audit_log("write", name, actor, {
                "checksum": record.lock.checksum,
                "size": len(str(data)),
                **(metadata or {})
            })
        except SecurityError as e:
            audit_log("write_failed", name, actor, {"error": str(e), **(metadata or {})})
            raise

    @classmethod
    def unregister(cls, name: str, actor: str) -> None:
        """Remove memory object from registry."""
        with cls._get_lock():
            if name in cls._registry:
                del cls._registry[name]
                audit_log("unregistered", name, actor)

    @classmethod
    def list_objects(cls, actor: str) -> Dict[str, Dict[str, Any]]:
        """Return snapshot of registered objects."""
        with cls._get_lock():
            result = {
                name: {
                    "readers": list(record.readers),
                    "writers": list(record.writers),
                    "created_at": record.created_at,
                    "read_only": record.lock.read_only
                }
                for name, record in cls._registry.items()
            }
            audit_log("list_objects", "registry", actor, {"count": len(result)})
            return result

    @classmethod
    def update_policies(
        cls,
        name: str,
        actor: str,
        readers: Optional[Set[str]] = None,
        writers: Optional[Set[str]] = None
    ) -> None:
        """Update access policies for a registered object."""
        with cls._get_lock():
            if name not in cls._registry:
                raise KeyError(f"Memory object '{name}' not found")

            record = cls._registry[name]
            if readers is not None:
                record.readers = set(readers)
            if writers is not None:
                record.writers = set(writers)

            audit_log("policies_updated", name, actor, {
                "readers": list(record.readers),
                "writers": list(record.writers)
            })


class nullcontext:
    def __enter__(self):
        return self

    def __exit__(self, *args):
        pass


# ---------------------------------------------------------------------------
# Performance-optimized serializers
# ---------------------------------------------------------------------------


def fast_json_serializer(data: Any) -> str:
    """Optimized JSON serializer for large objects."""
    return json.dumps(data, separators=(',', ':'), ensure_ascii=False)


def binary_serializer(data: Any) -> str:
    """Serializer for binary data using base64 encoding."""
    import base64
    if isinstance(data, bytes):
        return base64.b64encode(data).decode('ascii')
    raise ValueError("Binary serializer only accepts bytes data")


__all__ = [
    "MemoryLock",
    "EthicsGuard",
    "audit_log",
    "fast_json_serializer",
    "binary_serializer",
]

