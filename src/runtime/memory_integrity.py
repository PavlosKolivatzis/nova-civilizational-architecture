"""Memory integrity utilities with performance monitoring.

This module re-exports the memory lock and ethics guard utilities from the
Slot 8 implementation and attaches lightweight performance tracking.
"""

from nova.slots.slot08_memory_ethics.lock_guard import (
    MemoryLock,
    EthicsGuard,
    SecurityError,
    MemoryTamperError,
    RegistrationError,
    ENABLE_CHECKSUM_ON_READ,
    audit_log,
)

import time
from typing import Dict, List


class PerformanceMonitor:
    """Simple performance tracker for memory operations."""

    _counts: Dict[str, int] = {}
    _timings: Dict[str, List[float]] = {}

    @classmethod
    def track(cls, operation: str, duration: float) -> None:
        """Track operation count and timing."""
        cls._counts[operation] = cls._counts.get(operation, 0) + 1
        cls._timings.setdefault(operation, []).append(duration)
        if len(cls._timings[operation]) > 1000:
            cls._timings[operation] = cls._timings[operation][-1000:]

    @classmethod
    def get_stats(cls, operation: str) -> Dict[str, float]:
        """Return performance statistics for an operation."""
        timings = cls._timings.get(operation, [])
        if not timings:
            return {}

        sorted_timings = sorted(timings)
        count = len(sorted_timings)
        p95_index = max(int(count * 0.95) - 1, 0)
        return {
            "count": cls._counts.get(operation, 0),
            "avg_ms": sum(sorted_timings) / count * 1000,
            "p95_ms": sorted_timings[p95_index] * 1000,
            "max_ms": sorted_timings[-1] * 1000,
        }

    @classmethod
    def get_all_stats(cls) -> Dict[str, Dict[str, float]]:
        """Return stats for all tracked operations."""
        return {op: cls.get_stats(op) for op in cls._counts}

    @classmethod
    def clear(cls) -> None:
        """Clear all tracked statistics."""
        cls._counts.clear()
        cls._timings.clear()


def with_performance_monitoring(func):
    """Decorator to track performance of EthicsGuard methods."""

    def wrapper(*args, **kwargs):
        start_time = time.time()
        try:
            return func(*args, **kwargs)
        finally:
            duration = time.time() - start_time
            PerformanceMonitor.track(func.__name__, duration)

    return wrapper


# Apply performance monitoring to core methods
for _name in ["read", "write", "unregister"]:
    if hasattr(EthicsGuard, _name):
        setattr(EthicsGuard, _name, with_performance_monitoring(getattr(EthicsGuard, _name)))


# Wrap register to enforce actor presence before applying monitoring
_original_register = EthicsGuard.register

def _register_with_validation(*args, **kwargs):
    if kwargs.get("actor") is None:
        raise ValueError("Actor is required")
    return _original_register(*args, **kwargs)

EthicsGuard.register = with_performance_monitoring(_register_with_validation)


__all__ = [
    "MemoryLock",
    "EthicsGuard",
    "SecurityError",
    "MemoryTamperError",
    "RegistrationError",
    "ENABLE_CHECKSUM_ON_READ",
    "audit_log",
    "PerformanceMonitor",
]
