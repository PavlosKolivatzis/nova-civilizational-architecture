"""Adaptive routing logic with timeout normalization and circuit breaker support."""

import logging
from typing import Optional, Tuple

from nova.orchestrator.core.circuit_breaker import CircuitBreaker, CircuitBreakerError
from ..config import config

logger = logging.getLogger("router")


class AdaptiveRouter:
    """Enhanced router with timeout normalization and safety caps.

    Always returns ``(slot, timeout_s)`` tuple.
    """

    def __init__(
        self,
        performance_monitor,
        latency_threshold_ms: Optional[float] = None,
        error_threshold: Optional[float] = None,
        circuit_breaker: Optional[CircuitBreaker] = None,
    ) -> None:
        self.monitor = performance_monitor
        self.latency_threshold_ms = latency_threshold_ms or config.ROUTER_LATENCY_MS
        self.error_threshold = error_threshold or config.ROUTER_ERROR_THRESHOLD
        self.cb = circuit_breaker
        self.fallback_map: dict[str, str] = {}
        self.multiplier = config.ROUTER_TIMEOUT_MULTIPLIER
        self.timeout_cap = config.ROUTER_TIMEOUT_CAP_S

    def _normalize_timeout(self, slot: str, original_timeout: Optional[float]) -> float:
        """Normalize timeout based on history or provided value."""
        if original_timeout is None:
            health = self.monitor.get_slot_health(slot)
            avg_latency_ms = health.get("avg_latency_ms", 1000)
            timeout_s = (avg_latency_ms / 1000) * self.multiplier
        else:
            timeout_s = original_timeout * self.multiplier
        return min(timeout_s, self.timeout_cap)

    def get_route(self, target_slot: str, original_timeout: Optional[float] = None) -> Tuple[str, float]:
        """Get route for target slot with normalized timeout."""
        if self.cb and self.cb.should_block(target_slot):
            fb = self.fallback_map.get(target_slot)
            if fb:
                return fb, self._normalize_timeout(fb, original_timeout)
            raise CircuitBreakerError(f"slot {target_slot} blocked")

        actual_slot = target_slot
        if target_slot in self.fallback_map:
            health = self.monitor.get_slot_health(target_slot)
            if (
                health.get("avg_latency_ms", 0) > self.latency_threshold_ms
                or health.get("error_rate", 0) > self.error_threshold
            ):
                actual_slot = self.fallback_map[target_slot]
                logger.info(f"Routing to fallback {actual_slot} for {target_slot}")

        timeout_s = self._normalize_timeout(actual_slot, original_timeout)
        logger.debug(f"Routed {target_slot} -> {actual_slot} with timeout {timeout_s}s")
        return actual_slot, timeout_s
