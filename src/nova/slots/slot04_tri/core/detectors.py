from __future__ import annotations
from collections import deque
import time
import math
from typing import Optional, Dict, Any

class DriftDetector:
    """
    True rolling mean/std z-score drift detector with O(1) updates.
    """
    def __init__(self, window: int = 200, z_threshold: float = 3.0, min_warm_frac: float = 0.2):
        self.window = window
        self.z_threshold = z_threshold
        self.q: deque[float] = deque(maxlen=window)
        self._sum = 0.0
        self._sum2 = 0.0
        self._min_warm = max(10, int(min_warm_frac * window))

    def update(self, value: float) -> Optional[Dict[str, Any]]:
        # Figure out if we will evict before append (deque doesn't return popped)
        popped: Optional[float] = self.q[0] if len(self.q) == self.q.maxlen else None
        if popped is not None:
            # We'll lose leftmost after append; pre-subtract it
            self._sum -= popped
            self._sum2 -= popped * popped
        # Append and add new sample
        self.q.append(value)
        self._sum += value
        self._sum2 += value * value

        n = len(self.q)
        if n < 2:
            return None
        mean = self._sum / n
        # Unbiased sample variance from rolling sums
        var = max(0.0, (self._sum2 / n) - (mean * mean))
        if n > 1:
            var *= n / (n - 1)
        std = math.sqrt(var)
        z = 0.0 if std == 0.0 else abs((value - mean) / (std + 1e-12))

        if n >= self._min_warm and z >= self.z_threshold:
            return {
                "type": "tri_drift",
                "z": z,
                "mean": mean,
                "std": std,
                "n": n,
                "ts": time.time(),
            }
        return None

class SurgeDetector:
    def __init__(self, window: int = 10, threshold: int = 50, cooldown_s: float = 0.0):
        self.window = window
        self.threshold = threshold
        self.cooldown_s = cooldown_s
        self.events: deque[int] = deque(maxlen=window)
        self._sum = 0
        self._last_ts = 0.0

    def tick(self, count: int, *, now: Optional[float] = None, threshold: Optional[int] = None) -> Optional[Dict[str, Any]]:
        """
        Push a new count (e.g., writes in last second). Returns an event dict on trigger else None.
        Uses O(1) rolling sum and enforces cooldown and warmup (armed when window is full).
        """
        now = time.time() if now is None else now
        # sanitize
        if count < 0:
            count = 0
        # pre-subtract if queue full and about to evict
        if len(self.events) == self.events.maxlen:
            self._sum -= self.events[0]
        self.events.append(count)
        self._sum += count
        eff_thr = self.threshold if threshold is None else threshold
        armed = len(self.events) == self.events.maxlen
        if armed and self._sum > eff_thr and (now - self._last_ts) >= self.cooldown_s:
            self._last_ts = now
            return {
                "type": "throughput_surge",
                "window_sec": self.window,
                "window_sum": self._sum,
                "threshold": eff_thr,
                "margin": self._sum - eff_thr,
                "ts": now,
            }
        return None
