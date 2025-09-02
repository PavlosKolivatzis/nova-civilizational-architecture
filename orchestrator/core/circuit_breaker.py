import time
from typing import Dict, Any


class CircuitBreakerError(RuntimeError):
    pass


class CircuitBreaker:
    def __init__(self, monitor, error_threshold: float = 0.5, recovery_time: int = 60) -> None:
        self.monitor = monitor
        self.error_threshold = error_threshold
        self.recovery_time = recovery_time
        self._tripped: dict[str, float] = {}
        self._trip_count = 0

    def should_block(self, slot_id: str) -> bool:
        now = time.time()
        ts = self._tripped.get(slot_id)
        if ts and now - ts < self.recovery_time:
            return True
        if ts and now - ts >= self.recovery_time:
            del self._tripped[slot_id]
        h = self.monitor.get_slot_health(slot_id)
        if h["error_rate"] > self.error_threshold:
            self._tripped[slot_id] = now
            self._trip_count += 1
            return True
        return False

    def get_metrics(self) -> Dict[str, Any]:
        return {
            "tripped_slots": list(self._tripped.keys()),
            "trip_count": self._trip_count,
            "recovery_time_seconds": self.recovery_time,
            "error_threshold": self.error_threshold,
        }
