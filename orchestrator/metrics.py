"""Centralized metrics for NOVA system components."""

import threading
from typing import Dict, Any, Optional, List, Deque
from datetime import datetime, timezone
from collections import deque
import math


class Slot6Metrics:
    """Thread-safe metrics collection for Slot 6 Cultural Synthesis."""

    def __init__(self, window: int = 256):
        self._lock = threading.RLock()
        self._decisions = {"approved": 0, "transform": 0, "blocked": 0}
        self._legacy_calls = 0
        self._last_decision: Optional[Dict[str, Any]] = None
        self._window = max(8, int(window))
        self._residual_risk: Deque[float] = deque(maxlen=self._window)
        self._last_updated: Optional[datetime] = None

    def record_decision(self, result_name: str, pps: float, residual_risk: float, **metadata):
        """Record a cultural synthesis decision."""
        with self._lock:
            # Normalize result name for counting
            key = result_name.lower().replace("_", "").replace("-", "")
            if "approved" in key:
                self._decisions["approved"] += 1
            elif "transform" in key or "requires" in key:
                self._decisions["transform"] += 1
            elif "blocked" in key:
                self._decisions["blocked"] += 1

            # Store last decision details
            self._last_decision = {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "result": result_name,
                "pps": round(pps, 3),
                "residual_risk": round(residual_risk, 3),
                "metadata": metadata
            }

            # Track residual risk for percentile calculation
            self._residual_risk.append(float(residual_risk))
            self._last_updated = datetime.now(timezone.utc)

    def record_legacy_call(self):
        """Record a legacy API usage."""
        with self._lock:
            self._legacy_calls += 1

    def _percentile(self, data: List[float], p: float) -> float:
        """Inclusive linear interpolation percentile (no numpy)."""
        if not data:
            return float("nan")
        x = sorted(data)
        if p <= 0:
            return x[0]
        if p >= 100:
            return x[-1]
        k = (p / 100.0) * (len(x) - 1)
        f = math.floor(k)
        c = math.ceil(k)
        if f == c:
            return x[int(k)]
        return x[f] + (k - f) * (x[c] - x[f])

    def p95_residual_risk(self) -> Optional[float]:
        """Calculate 95th percentile of residual risk from rolling window."""
        with self._lock:
            data = list(self._residual_risk)
        if not data:
            return None
        return self._percentile(data, 95.0)

    def get_metrics(self) -> Dict[str, Any]:
        """Get current metrics snapshot."""
        with self._lock:
            return {
                "version": "v7.4.1",
                "decisions_total": sum(self._decisions.values()),
                "decisions": dict(self._decisions),
                "legacy_calls_total": self._legacy_calls,
                "last_decision": dict(self._last_decision) if self._last_decision else None,
                "p95_residual_risk": self.p95_residual_risk(),
            }

    def reset(self):
        """Reset all counters (for testing)."""
        with self._lock:
            self._decisions = {"approved": 0, "transform": 0, "blocked": 0}
            self._legacy_calls = 0
            self._last_decision = None
            self._residual_risk.clear()
            self._last_updated = None


# Global instance
slot6_metrics = Slot6Metrics()


def get_slot6_metrics() -> Slot6Metrics:
    """Get the global Slot 6 metrics instance."""
    return slot6_metrics
