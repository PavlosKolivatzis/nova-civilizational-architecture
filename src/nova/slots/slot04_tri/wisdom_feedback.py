"""
TRI → Wisdom Governor feedback loop.

Provides coherence-based η (learning rate) cap for the adaptive wisdom governor.
High coherence (stable system) → allow higher learning rates.
Low coherence (unstable system) → cap learning rates lower for safety.

Design:
- Coherence C ∈ [0, 1] computed by TRI engine as C = 1/(1 + cv)
- Maps C to η_cap via piecewise linear function
- Integrates with governor via max cap on set_eta()

Formula:
- C > 0.85 (very stable) → η_cap = 0.18 (high exploration)
- C < 0.40 (unstable) → η_cap = 0.08 (conservative)
- 0.40 ≤ C ≤ 0.85 → linear interpolation
"""

from __future__ import annotations

import os
from typing import Optional

__all__ = ["compute_tri_eta_cap", "get_tri_coherence", "get_feedback_config"]


def get_feedback_config() -> tuple[float, float, float, float]:
    """
    Get TRI feedback configuration from environment.

    Returns:
        tuple[float, float, float, float]: (
            coherence_high_threshold,
            coherence_low_threshold,
            eta_cap_high,
            eta_cap_low
        )
    """
    high_threshold = float(os.getenv("NOVA_TRI_COHERENCE_HIGH", "0.85"))
    low_threshold = float(os.getenv("NOVA_TRI_COHERENCE_LOW", "0.40"))
    eta_cap_high = float(os.getenv("NOVA_TRI_ETA_CAP_HIGH", "0.18"))
    eta_cap_low = float(os.getenv("NOVA_TRI_ETA_CAP_LOW", "0.08"))

    # Safety: ensure thresholds are ordered
    if low_threshold >= high_threshold:
        low_threshold = high_threshold - 0.1

    return (high_threshold, low_threshold, eta_cap_high, eta_cap_low)


def compute_tri_eta_cap(coherence: float) -> float:
    """
    Compute learning rate cap based on TRI coherence.

    This implements the feedback loop from Slot 4 (TRI) to the wisdom governor.
    Higher coherence (more stable token distribution) allows higher learning rates.

    Args:
        coherence: TRI coherence score ∈ [0, 1]

    Returns:
        float: Maximum allowed learning rate η_cap

    Example:
        >>> compute_tri_eta_cap(0.90)  # Very stable
        0.18
        >>> compute_tri_eta_cap(0.30)  # Unstable
        0.08
        >>> compute_tri_eta_cap(0.625)  # Mid-range
        0.13  # Linear interpolation
    """
    high_thresh, low_thresh, eta_high, eta_low = get_feedback_config()

    # Clamp coherence to [0, 1]
    C = max(0.0, min(1.0, coherence))

    # Piecewise linear mapping
    if C >= high_thresh:
        # Very stable → allow high exploration
        return eta_high
    elif C <= low_thresh:
        # Unstable → conservative cap
        return eta_low
    else:
        # Linear interpolation
        # η_cap = eta_low + (C - low_thresh) / (high_thresh - low_thresh) * (eta_high - eta_low)
        slope = (eta_high - eta_low) / (high_thresh - low_thresh)
        return eta_low + slope * (C - low_thresh)


def get_tri_coherence() -> Optional[float]:
    """
    Attempt to read current coherence from TRI engine or semantic mirror.

    Returns:
        Optional[float]: Coherence ∈ [0, 1], or None if unavailable
    """
    # Try reading from semantic mirror first (published by TRI assess())
    try:
        if os.getenv("NOVA_ENABLE_PROBABILISTIC_CONTRACTS", "1") == "1":
            from nova.orchestrator.semantic_mirror import get_semantic_mirror

            mirror = get_semantic_mirror()

            # Try reading coherence belief
            coherence_belief = mirror.consume_context("slot04.coherence")
            if coherence_belief is not None:
                # Extract mean from BeliefState or use scalar value
                if hasattr(coherence_belief, "mean"):
                    return float(coherence_belief.mean)
                else:
                    return float(coherence_belief)

            # Fallback: try reading tri_score (less ideal but available)
            tri_score = mirror.consume_context("slot04.tri_score")
            if tri_score is not None:
                # Use tri_score as proxy (not ideal, but better than nothing)
                return float(tri_score) if isinstance(tri_score, (int, float)) else None

    except (ImportError, Exception):
        pass

    # No coherence available
    return None


def get_feedback_status() -> dict:
    """
    Get current TRI feedback status for monitoring/debugging.

    Returns:
        dict: Status including coherence, eta_cap, configuration
    """
    coherence = get_tri_coherence()
    eta_cap = compute_tri_eta_cap(coherence) if coherence is not None else None

    high_thresh, low_thresh, eta_high, eta_low = get_feedback_config()

    return {
        "coherence": coherence,
        "eta_cap": eta_cap,
        "available": coherence is not None,
        "config": {
            "coherence_high_threshold": high_thresh,
            "coherence_low_threshold": low_thresh,
            "eta_cap_high": eta_high,
            "eta_cap_low": eta_low,
        },
    }
