"""Slot06 receiver for unlearn pulse fanout."""

import logging
from typing import Any
from orchestrator.contracts.emitter import subscribe
from orchestrator.contracts.decay import pulse_weight_decay
import time

logger = logging.getLogger(__name__)

_last_pulse_time = 0
_pulse_count = 0


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

    # Apply exponential decay based on contract age
    base_weight = 1.0
    effective_weight = pulse_weight_decay(
        pulse_strength=base_weight,
        age_seconds=contract_age,
        half_life=300.0  # 5-minute half-life
    )

    _pulse_count += 1
    _last_pulse_time = current_time

    logger.info(
        f"Slot06 decay: key={getattr(contract, 'key', 'unknown')} "
        f"old={base_weight:.6f} new={effective_weight:.6f} age={contract_age:.1f}s"
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


__all__ = ["handle_unlearn_pulse", "register_slot06_receiver", "get_pulse_metrics"]