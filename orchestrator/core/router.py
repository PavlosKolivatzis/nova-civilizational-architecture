from typing import Optional, Tuple

from orchestrator.core.circuit_breaker import CircuitBreaker, CircuitBreakerError


class AdaptiveRouter:
    def __init__(
        self,
        performance_monitor,
        latency_threshold_ms: float = 1000.0,
        error_threshold: float = 0.2,
        circuit_breaker: Optional[CircuitBreaker] = None,
    ) -> None:
        self.monitor = performance_monitor
        self.latency_threshold_ms = latency_threshold_ms
        self.error_threshold = error_threshold
        self.cb = circuit_breaker
        self.fallback_map = {}

    def get_route(
        self, target_slot: str, original_timeout: float | None = None
    ) -> Tuple[str, float | None]:
        if self.cb and self.cb.should_block(target_slot):
            fb = self.fallback_map.get(target_slot)
            if fb:
                return fb, original_timeout
            raise CircuitBreakerError(f"slot {target_slot} blocked")

        health = self.monitor.get_slot_health(target_slot)
        timeout_s = max(
            original_timeout or 2.0, (health["avg_latency_ms"] * 1.5) / 1000.0
        )
        if timeout_s > 30.0:
            timeout_s = 30.0

        chosen = target_slot
        if (
            health["avg_latency_ms"] > self.latency_threshold_ms
            or health["error_rate"] > self.error_threshold
        ):
            fb = self.fallback_map.get(target_slot)
            if fb:
                chosen = fb
        return chosen, timeout_s
