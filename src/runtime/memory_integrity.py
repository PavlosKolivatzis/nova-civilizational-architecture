"""Memory integrity utilities with performance monitoring.

This module re-exports the memory lock and ethics guard utilities from the
Slot 8 implementation and attaches lightweight performance tracking.
"""

from slots.slot08_memory_ethics.lock_guard import (
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
        return {
            "count": cls._counts.get(operation, 0),
            "avg_ms": sum(timings) / len(timings) * 1000,
            "p95_ms": sorted(timings)[int(len(timings) * 0.95)] * 1000,
            "max_ms": max(timings) * 1000,
            "recent_samples": len(timings),
        }

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
