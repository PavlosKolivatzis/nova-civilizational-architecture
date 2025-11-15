from __future__ import annotations
import contextlib
import time
from typing import Optional

class SafeMode:
    def __init__(self, flip_max_s: float = 0.5, max_duration_s: Optional[float] = None):
        self.active: bool = False
        self._flip_max_s: float = float(flip_max_s)
        self._max_duration_s: Optional[float] = float(max_duration_s) if max_duration_s is not None else None
        # monotonic for durations, wall for stamps
        self._t0_mon: Optional[float] = None
        self._t0_wall: Optional[float] = None
        # trace
        self._last_reason: Optional[str] = None
        self._flip_overruns: int = 0

    def activate(self, reason: Optional[str] = None, *, force: bool = False) -> float:
        """
        Activate safe mode. Returns activation latency (seconds).
        Keeps test contract: float return; caller can compare with policy.safe_mode_flip_max_s.
        """
        if self.active and not force:
            # already active: zero-cost activation
            return 0.0
        t_start = time.perf_counter()
        # flip
        self.active = True
        self._t0_mon = time.monotonic()
        self._t0_wall = time.time()
        self._last_reason = reason
        dt = time.perf_counter() - t_start
        if dt > self._flip_max_s:
            self._flip_overruns += 1
        return dt

    def deactivate(self):
        self.active = False
        self._t0_mon = None
        self._t0_wall = None
        self._last_reason = None

    # ---------- helpers ----------
    @property
    def active_for_s(self) -> float:
        """How long safe-mode has been active (0 if inactive)."""
        if not self.active or self._t0_mon is None:
            return 0.0
        return max(0.0, time.monotonic() - self._t0_mon)

    def expired(self) -> bool:
        """Whether active safe-mode exceeded max_duration_s (if configured)."""
        return bool(self.active and self._max_duration_s is not None and self.active_for_s > self._max_duration_s)

    def deactivate_if_expired(self) -> bool:
        """Deactivate when exceeded max_duration_s. Returns True if deactivated."""
        if self.expired():
            self.deactivate()
            return True
        return False

    def metrics(self) -> dict:
        """Lightweight snapshot for observability."""
        return {
            "active": self.active,
            "active_for_s": self.active_for_s,
            "flip_slo_s": self._flip_max_s,
            "max_duration_s": self._max_duration_s,
            "flip_overruns": self._flip_overruns,
            "reason": self._last_reason,
            "t0_wall": self._t0_wall,
        }

    @contextlib.contextmanager
    def activated(self, reason: Optional[str] = None):
        """Context manager that activates (optionally with a reason) and yields self."""
        self.activate(reason)
        try:
            yield self
        finally:
            self.deactivate()
