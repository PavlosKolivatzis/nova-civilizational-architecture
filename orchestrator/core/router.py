from typing import Optional


class AdaptiveRouter:
    def __init__(self, performance_monitor, latency_threshold_ms: float = 1000.0, error_threshold: float = 0.2) -> None:
        self.monitor = performance_monitor
        self.latency_threshold_ms = latency_threshold_ms
        self.error_threshold = error_threshold
        self.fallback_map = {}

    def get_route(self, target_slot: str) -> str:
        health = self.monitor.get_slot_health(target_slot)
        if (
            health["avg_latency_ms"] > self.latency_threshold_ms
            or health["error_rate"] > self.error_threshold
        ):
            fb = self.fallback_map.get(target_slot)
            if fb:
                return fb
        return target_slot
