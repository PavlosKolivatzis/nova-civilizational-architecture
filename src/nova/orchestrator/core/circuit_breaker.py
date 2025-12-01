import time
from contextlib import contextmanager
from typing import Any, Dict, Optional


class CircuitBreakerError(RuntimeError):
    """Raised when the circuit breaker blocks a slot."""
    pass


class CircuitBreaker:
    """Simple circuit breaker with optional monitor integration."""

    def __init__(
        self,
        monitor=None,
        error_threshold: float = 0.5,
        recovery_time: int = 60,
        failure_threshold: int = 5,
        reset_timeout: float = 60.0,
    ) -> None:
        self.monitor = monitor
        self.error_threshold = error_threshold
        self.recovery_time = recovery_time
        self._tripped: dict[str, float] = {}
        self._trip_count = 0

        self.failure_threshold = failure_threshold
        self.reset_timeout = reset_timeout
        self._state = "closed"
        self.failure_count = 0
        self.success_count = 0
        self.last_failure: Any = None
        self._opened_at: Optional[float] = None

    @property
    def state(self) -> str:
        if self._state == "open" and self._opened_at is not None:
            if time.time() - self._opened_at >= self.reset_timeout:
                self._state = "half-open"
        return self._state

    def should_block(self, slot_id: str) -> bool:
        now = time.time()
        ts = self._tripped.get(slot_id)
        if ts and now - ts < self.recovery_time:
            return True
        if ts and now - ts >= self.recovery_time:
            del self._tripped[slot_id]
        if not self.monitor:
            return False
        h = self.monitor.get_slot_health(slot_id)
        if h["error_rate"] > self.error_threshold:
            self._tripped[slot_id] = now
            self._trip_count += 1
            return True
        return False

    @contextmanager
    def protect(self):
        if self.state == "open":
            raise Exception("Circuit is open")
        try:
            yield
        except Exception as exc:  # pragma: no cover - behavior tested via chaos tests
            self.failure_count += 1
            self.last_failure = exc
            if self.failure_count >= self.failure_threshold:
                self._state = "open"
                self._opened_at = time.time()
            raise
        else:
            self.success_count += 1
            if self.state == "half-open":
                self._state = "closed"
                self.failure_count = 0

    def get_metrics(self) -> Dict[str, Any]:
        metrics = {
            "tripped_slots": list(self._tripped.keys()),
            "trip_count": self._trip_count,
            "recovery_time_seconds": self.recovery_time,
            "error_threshold": self.error_threshold,
            "state": self.state,
            "failure_count": self.failure_count,
            "success_count": self.success_count,
        }
        if self.last_failure:
            metrics["last_failure"] = str(self.last_failure)
        return metrics
