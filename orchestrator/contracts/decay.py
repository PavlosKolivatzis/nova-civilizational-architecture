"""Exponential weight decay utility for unlearn pulse handling."""

import math
from typing import Optional


def exponential_decay(
    base_weight: float = 1.0,
    decay_rate: float = 0.1,
    time_delta: float = 1.0,
    min_weight: Optional[float] = None
) -> float:
    """
    Calculate exponential weight decay for unlearn pulse processing.

    Args:
        base_weight: Initial weight value
        decay_rate: Rate of decay (0.0 = no decay, 1.0 = instant decay)
        time_delta: Time elapsed since base measurement
        min_weight: Optional minimum weight floor

    Returns:
        Decayed weight value
    """
    if decay_rate <= 0:
        return base_weight

    decayed = base_weight * math.exp(-decay_rate * time_delta)

    if min_weight is not None:
        decayed = max(decayed, min_weight)

    return decayed


def pulse_weight_decay(
    pulse_strength: float,
    age_seconds: float,
    half_life: float = 300.0  # 5 minutes default
) -> float:
    """
    Calculate decayed pulse weight using half-life model.

    Args:
        pulse_strength: Original pulse strength
        age_seconds: Age of pulse in seconds
        half_life: Time for weight to decay to 50% (seconds)

    Returns:
        Current effective pulse weight
    """
    if half_life <= 0:
        return pulse_strength

    decay_rate = math.log(2) / half_life
    return exponential_decay(pulse_strength, decay_rate, age_seconds)


__all__ = ["exponential_decay", "pulse_weight_decay"]