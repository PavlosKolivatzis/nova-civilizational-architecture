"""Slot7 reflex back-pressure system for stress coordination.

This module implements reflex signaling from Slot7 production controls to downstream
slots (primarily Slot6 cultural synthesis) during system pressure conditions.

The reflex system provides rapid coordination between production and cultural layers,
allowing for adaptive behavior during stress without complex orchestration.
"""

import logging
import os
import time
from typing import Optional

logger = logging.getLogger(__name__)

# Configuration
REFLEX_THRESHOLD = float(os.getenv("NOVA_SLOT07_REFLEX_THRESHOLD", "0.70"))  # when to emit max backpressure
REFLEX_SLOPE = float(os.getenv("NOVA_SLOT07_REFLEX_SLOPE", "1.50"))         # pressure → backpressure mapping


def emit_backpressure(level: float, reason: str = "load") -> None:
    """Emit reflex back-pressure signal to coordinate downstream slots.

    Args:
        level: Pressure level ∈ [0,1] (0=no pressure, 1=max pressure)
        reason: Human-readable reason for back-pressure ("load", "errors", "latency")
    """
    try:
        from orchestrator.semantic_mirror import publish

        # Clamp level to safe bounds
        level = max(0.0, min(1.0, float(level)))

        # Publish reflex signal with short TTL for responsiveness
        publish(
            "slot07.backpressure",
            {
                "level": level,
                "reason": str(reason),
                "timestamp": time.time(),
            },
            "slot07_production_controls",
            ttl=60.0,  # 1-minute TTL for rapid coordination
        )

        logger.info(f"Slot7 reflex: emitted backpressure={level:.3f} reason={reason}")

    except Exception as e:
        logger.warning(f"Failed to emit reflex backpressure: {e}")


def compute_backpressure_level(pressure: float, error_rate: float = 0.0) -> float:
    """Compute reflex back-pressure level from system metrics.

    Args:
        pressure: System pressure level ∈ [0,1]
        error_rate: Error rate ∈ [0,1] (optional boost factor)

    Returns:
        Back-pressure level ∈ [0,1] for emission
    """
    # Base mapping: pressure above threshold → linear scale to max backpressure
    if pressure <= REFLEX_THRESHOLD:
        base_level = 0.0
    else:
        excess = pressure - REFLEX_THRESHOLD
        max_excess = 1.0 - REFLEX_THRESHOLD
        base_level = min(1.0, (excess / max_excess) * REFLEX_SLOPE)

    # Error rate boost (additive)
    error_boost = min(0.3, error_rate * 0.5)  # cap at 30% boost

    return min(1.0, base_level + error_boost)


def get_current_backpressure() -> Optional[dict]:
    """Read current back-pressure state from semantic mirror.

    Returns:
        Dict with level, reason, timestamp or None if no active signal
    """
    try:
        from orchestrator.semantic_mirror import get_context
        return get_context("slot07.backpressure")
    except Exception as e:
        logger.warning(f"Failed to read backpressure state: {e}")
        return None


def update_reflex_metrics(level: float, reason: str) -> None:
    """Update Prometheus metrics for reflex system observability."""
    try:
        # Import locally to avoid hard dependency
        from orchestrator.prometheus_metrics import reflex_backpressure_gauge, reflex_emissions_counter

        reflex_backpressure_gauge.set(level)
        reflex_emissions_counter.labels(reason=reason).inc()

    except Exception as e:
        logger.debug(f"Reflex metrics update failed: {e}")
