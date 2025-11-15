"""Slot06 receiver for unlearn pulse fanout."""

import logging
from typing import Any
from orchestrator.contracts.emitter import subscribe
from orchestrator.contracts.decay import pulse_weight_decay
from orchestrator.unlearn_weighting import get_anomaly_multiplier, get_dynamic_half_life
import time

logger = logging.getLogger(__name__)

_last_pulse_time = 0
_pulse_count = 0
_metrics = {"decay_events": 0, "decay_amount": 0.0}  # events, sum(old-new)


def _read_backpressure() -> float:
    """Read Slot7 reflex back-pressure level from semantic mirror.

    Returns:
        Back-pressure level ∈ [0,1] (0=no pressure, 1=max pressure)
    """
    try:
        from orchestrator.semantic_mirror import get_context
        ctx = get_context("slot07.backpressure") or {}
        level = float(ctx.get("level", 0.0))
        return max(0.0, min(1.0, level))
    except Exception as e:
        logger.debug(f"Failed to read backpressure: {e}")
        return 0.0


def handle_unlearn_pulse(contract: Any) -> None:
    """
    Handle incoming unlearn pulse with exponential weight decay.

    Args:
        contract: The contract/pulse data received
    """
    global _last_pulse_time, _pulse_count

    current_time = time.time()

    # Extract age from contract (age since context creation/expiry)
    contract_age = float(getattr(contract, "age_seconds", 0.0))

    # Read Slot7 reflex back-pressure for coordination
    backpressure_level = _read_backpressure()

    # Apply anomaly multiplier then exponential decay based on contract age
    base_weight = 1.0 * get_anomaly_multiplier(slot="slot06")
    half_life = get_dynamic_half_life(base_half_life=300.0, slot="slot06")  # Phase 4.1: dynamic half-life

    # Reflex back-pressure: reduce half-life up to 20% under full pressure
    half_life *= (1.0 - 0.20 * backpressure_level)

    effective_weight = pulse_weight_decay(
        pulse_strength=base_weight,
        age_seconds=contract_age,
        half_life=half_life
    )

    # record metrics (amount is strictly non-negative)
    try:
        decay_amount = max(0.0, float(base_weight) - float(effective_weight))
    except Exception:
        decay_amount = 0.0
    _metrics["decay_events"] += 1
    _metrics["decay_amount"] += decay_amount
    _metrics["_last_backpressure"] = backpressure_level  # Track for observability

    _pulse_count += 1
    _last_pulse_time = current_time

    logger.info(
        f"Slot06 decay: key={getattr(contract, 'key', 'unknown')} "
        f"old={base_weight:.6f} new={effective_weight:.6f} age={contract_age:.1f}s "
        f"backpressure={backpressure_level:.3f}"
    )

    # Cultural synthesis could react to the pulse here
    # e.g., update synthesis weights, trigger recomputation, etc.


def register_slot06_receiver() -> None:
    """Register Slot06 as receiver for unlearn pulse fanout."""
    subscribe(handle_unlearn_pulse)
    logger.info("Slot06 unlearn pulse receiver registered")


def get_pulse_metrics() -> dict:
    """Get current pulse reception metrics for Slot06."""
    return {
        "pulse_count": _pulse_count,
        "last_pulse_time": _last_pulse_time,
        "time_since_last": time.time() - _last_pulse_time if _last_pulse_time else 0,
    }


def get_slot6_decay_metrics() -> dict:
    """Snapshot of Slot6 decay metrics for Prometheus exporter."""
    return dict(_metrics)


__all__ = ["handle_unlearn_pulse", "register_slot06_receiver", "get_pulse_metrics", "get_slot6_decay_metrics"]
