from __future__ import annotations

import copy
import threading
from dataclasses import dataclass, field
from typing import Any, Dict

from .lock import RealityLock


@dataclass
class RealityVerifier:
    """Thread-safe verifier for :class:`RealityLock` instances.

    The verifier minimizes lock contention by copying the ``RealityLock``
    under a short-lived lock and performing the expensive integrity check
    without holding the lock. Only metrics updates and result assembly are
    performed while the internal lock is held.
    """

    reality_lock: RealityLock
    metrics: Dict[str, int] = field(default_factory=lambda: {"verifications": 0, "failures": 0})
    _lock: threading.Lock = field(default_factory=threading.Lock, init=False)

    def verify(self) -> Dict[str, Any]:
        """Verify the underlying ``RealityLock`` while reducing contention."""
        with self._lock:
            lock_copy = copy.copy(self.reality_lock)
        valid = lock_copy.verify_integrity()
        with self._lock:
            self.metrics["verifications"] += 1
            if not valid:
                self.metrics["failures"] += 1
            result = {"valid": valid, "anchor": lock_copy.anchor}
        return result

    def get_metrics(self) -> Dict[str, int]:
        """Return a snapshot of verification metrics."""
        with self._lock:
            return dict(self.metrics)
