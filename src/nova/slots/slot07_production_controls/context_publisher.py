"""
Slot 7 Production Controls - Context Publisher

Publishes production control state to the Semantic Mirror for other slots
to make context-aware decisions. Provides breaker state, pressure levels,
and resource status information.
"""
import os
import time
import logging
from typing import Dict, Any, Optional
from dataclasses import dataclass

from nova.orchestrator.semantic_mirror import get_semantic_mirror, ContextScope

logger = logging.getLogger(__name__)


class _NoopReflexEmitter:
    """Noop reflex emitter for testing and fallback scenarios."""
    def get_metrics(self):
        return {"signals_emitted_by_type": {}}

    def emit(self, event: str, payload=None) -> None:
        pass


def get_reflex_emitter():
    """
    Factory for the process-wide reflex emitter.
    Tests patch this symbol directly.
    """
    try:
        # Try to import the actual reflex emitter
        from nova.slots.slot07_production_controls.reflex_emitter import get_reflex_emitter as get_real_emitter
        return get_real_emitter()
    except ImportError:
        # Fallback to noop emitter if reflex module not available
        return _NoopReflexEmitter()


@dataclass
class ProductionControlContext:
    """Context data published by Slot 7."""
    breaker_state: str  # "closed", "open", "half-open"
    pressure_level: float  # 0.0-1.0
    resource_utilization: float  # 0.0-1.0
    active_requests: int
    success_rate: float  # 0.0-1.0
    last_trip_timestamp: Optional[float]
    reflex_emissions_recent: int
    safeguards_active: list
    timestamp: float


class ProductionControlContextPublisher:
    """Publishes Slot 7 context to the Semantic Mirror."""

    def __init__(self, engine=None, publish_interval_seconds: float = 10.0):
        self.engine = engine  # ProductionControlEngine instance
        self.publish_interval_seconds = publish_interval_seconds
        self.last_publish = 0.0
        self.semantic_mirror = get_semantic_mirror()

        logger.info("Production Control Context Publisher initialized")

    def set_engine(self, engine) -> None:
        """Set the production control engine reference."""
        self.engine = engine

    def publish_context(self, force: bool = False) -> bool:
        """Publish current production control context.

        Args:
            force: Force publication even if interval hasn't elapsed

        Returns:
            True if context was published, False otherwise
        """
        current_time = time.time()

        # Check publish interval (unless forced)
        if not force and (current_time - self.last_publish) < self.publish_interval_seconds:
            return False

        if not self.engine:
            logger.warning("No production control engine configured")
            return False

        try:
            # Gather context data
            context = self._gather_context_data()

            # Publish individual context keys
            success = True

            # Breaker state (critical for other slots)
            success &= self.semantic_mirror.publish_context(
                "slot07.breaker_state",
                context.breaker_state,
                "slot07_production_controls",
                ContextScope.INTERNAL,
                ttl_seconds=30.0  # Short TTL for real-time data
            )

            # Pressure level (for throttling decisions)
            success &= self.semantic_mirror.publish_context(
                "slot07.pressure_level",
                context.pressure_level,
                "slot07_production_controls",
                ContextScope.INTERNAL,
                ttl_seconds=30.0
            )

            # Resource utilization summary
            resource_status = {
                "utilization": context.resource_utilization,
                "active_requests": context.active_requests,
                "success_rate": context.success_rate,
                "safeguards_active": context.safeguards_active
            }

            success &= self.semantic_mirror.publish_context(
                "slot07.resource_status",
                resource_status,
                "slot07_production_controls",
                ContextScope.INTERNAL,
                ttl_seconds=60.0
            )

            # System health summary (broader context)
            health_summary = {
                "overall_status": "healthy" if context.breaker_state == "closed" and context.success_rate > 0.9 else "degraded",
                "recent_reflex_emissions": context.reflex_emissions_recent,
                "last_incident": context.last_trip_timestamp,
                "pressure_trend": self._calculate_pressure_trend()
            }

            success &= self.semantic_mirror.publish_context(
                "slot07.health_summary",
                health_summary,
                "slot07_production_controls",
                ContextScope.INTERNAL,
                ttl_seconds=120.0
            )
            # Light-Clock phase_lock integration (guarded by feature flag)
            if os.getenv("NOVA_LIGHTCLOCK_DEEP", "1") == "1":
                try:
                    phase_lock_value = self.engine.compute_phase_lock()
                    success &= self.semantic_mirror.publish_context(
                        "slot07.phase_lock",
                        phase_lock_value,
                        "slot07_production_controls",
                        ContextScope.INTERNAL,
                        ttl_seconds=300.0  # Light-Clock temporal coherence window
                    )
                    logger.debug(f"Published phase_lock value: {phase_lock_value}")
                except Exception as e:
                    logger.warning(f"Failed to publish phase_lock: {e}")

            if success:
                self.last_publish = current_time
                logger.debug("Published production control context to semantic mirror")

                # Notify reflex layer (patch target exists for tests)
                try:
                    emitter = get_reflex_emitter()
                    emitter.emit("slot07.context_published", {"source": "slot07"})
                except Exception:
                    # Never fail the pipeline due to emitter issues
                    pass
            else:
                logger.warning("Failed to publish some context data")

            return success

        except Exception as e:
            logger.error(f"Failed to publish production control context: {e}")
            return False

    def _gather_context_data(self) -> ProductionControlContext:
        """Gather current production control context data."""
        # Get comprehensive metrics from engine
        metrics = self.engine.get_comprehensive_metrics()
        self.engine.health_check()

        # Calculate pressure level (similar to health.py logic)
        pressure_level = self._calculate_pressure_level(metrics)

        # Get resource utilization
        resource_util = min(1.0, metrics.get("active_requests", 0) / max(1, metrics.get("max_concurrent_requests", 50)))

        # Get recent reflex emissions (using patchable function)
        try:
            reflex_emitter = get_reflex_emitter()
            reflex_metrics = reflex_emitter.get_metrics()
            recent_emissions = sum(reflex_metrics.get("signals_emitted_by_type", {}).values())
        except Exception:
            recent_emissions = 0

        return ProductionControlContext(
            breaker_state=self.engine.circuit_breaker.state,
            pressure_level=pressure_level,
            resource_utilization=resource_util,
            active_requests=metrics.get("active_requests", 0),
            success_rate=metrics.get("success_rate", 1.0),
            last_trip_timestamp=self.engine.circuit_breaker.last_failure_time,
            reflex_emissions_recent=recent_emissions,
            safeguards_active=metrics.get("safeguards_active", []),
            timestamp=time.time()
        )

    def _calculate_pressure_level(self, metrics: Dict[str, Any]) -> float:
        """Calculate system pressure level from metrics."""
        pressure_factors = []

        # Circuit breaker contribution
        if self.engine.circuit_breaker.state == "open":
            pressure_factors.append(1.0)
        elif self.engine.circuit_breaker.state == "half-open":
            pressure_factors.append(0.7)
        else:
            # Failure rate contribution when closed
            failure_rate = 1.0 - metrics.get("success_rate", 1.0)
            pressure_factors.append(min(1.0, failure_rate * 2.0))

        # Resource utilization contribution
        resource_pressure = metrics.get("active_requests", 0) / max(1, metrics.get("max_concurrent_requests", 50))
        pressure_factors.append(min(1.0, resource_pressure))

        # Rate limiting violations contribution
        rate_violations = metrics.get("rate_limit_violations", 0)
        if rate_violations > 0:
            pressure_factors.append(min(1.0, rate_violations / 10.0))

        # Return weighted average with bias toward highest pressure
        if not pressure_factors:
            return 0.0

        avg_pressure = sum(pressure_factors) / len(pressure_factors)
        max_pressure = max(pressure_factors)

        # Weight toward maximum pressure (70% max, 30% avg)
        return min(1.0, 0.7 * max_pressure + 0.3 * avg_pressure)

    def _calculate_pressure_trend(self) -> str:
        """Calculate pressure trend direction (rising/falling/stable)."""
        # Simple implementation - could be enhanced with historical data
        current_pressure = self._gather_context_data().pressure_level

        if current_pressure > 0.8:
            return "rising"
        elif current_pressure < 0.3:
            return "falling"
        else:
            return "stable"

    def get_published_context_summary(self) -> Dict[str, Any]:
        """Get summary of what context is currently published."""
        try:
            summary = self.semantic_mirror.get_context_summary("slot07_production_controls")
            slot7_contexts = {k: v for k, v in summary.items() if k.startswith("slot07.")}
            return slot7_contexts
        except Exception as e:
            logger.error(f"Failed to get context summary: {e}")
            return {}


# Global context publisher instance
_context_publisher: Optional[ProductionControlContextPublisher] = None


def get_context_publisher(engine=None) -> ProductionControlContextPublisher:
    """Get global production control context publisher."""
    global _context_publisher
    if _context_publisher is None:
        _context_publisher = ProductionControlContextPublisher(engine)
    elif engine and not _context_publisher.engine:
        _context_publisher.set_engine(engine)
    return _context_publisher


def publish_production_context(force: bool = False) -> bool:
    """Convenience function to publish production control context."""
    publisher = get_context_publisher()
    return publisher.publish_context(force=force)


def reset_context_publisher() -> None:
    """Reset global context publisher (for testing)."""
    global _context_publisher
    _context_publisher = None
