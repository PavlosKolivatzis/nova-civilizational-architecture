"""
Wisdom-aware backpressure for Slot 7 Production Controls.

Reduces job parallelism when the adaptive wisdom governor detects instability
or freezes learning due to bifurcation risk.

Design:
- Reads frozen state from GovernorState (single source of truth)
- Optionally reads stability margin S from adaptive_wisdom_poller
- Returns reduced max_concurrent_jobs when unstable

Safety:
- frozen=True → minimal parallelism (2-4 jobs, system in survival mode)
- S < 0.03 → reduced parallelism (25-50% of baseline)
- S >= 0.03 → normal parallelism (100% of baseline)
"""

from __future__ import annotations

import os
from typing import Tuple

from nova.governor import state as governor_state

__all__ = ["compute_max_concurrent_jobs", "get_backpressure_config"]


def get_backpressure_config() -> Tuple[int, int, int, float]:
    """
    Get backpressure configuration from environment.

    Returns:
        Tuple[int, int, int, float]: (baseline_jobs, frozen_jobs, reduced_jobs, stability_threshold)
    """
    baseline = int(os.getenv("NOVA_SLOT07_MAX_JOBS_BASELINE", "16"))
    frozen = int(os.getenv("NOVA_SLOT07_MAX_JOBS_FROZEN", "2"))
    reduced = int(os.getenv("NOVA_SLOT07_MAX_JOBS_REDUCED", "6"))
    threshold = float(os.getenv("NOVA_SLOT07_STABILITY_THRESHOLD", "0.03"))

    # Safety: ensure frozen < reduced < baseline
    frozen = max(1, min(frozen, baseline // 2))
    reduced = max(frozen + 1, min(reduced, baseline - 1))

    return (baseline, frozen, reduced, threshold)


def compute_max_concurrent_jobs(stability_margin: float | None = None) -> int:
    """
    Compute adaptive max concurrent jobs based on wisdom governor state.

    This function implements the "job policy gate" for Slot 7, reducing
    parallelism during instability to prevent cascading failures.

    Args:
        stability_margin: Optional override for S (if None, attempts to read from poller)

    Returns:
        int: Maximum number of concurrent jobs allowed

    Behavior:
        - frozen=True → frozen_jobs (minimal, ~2)
        - S < threshold (default 0.03) → reduced_jobs (50% capacity, ~6)
        - S >= threshold → baseline_jobs (full capacity, ~16)
    """
    baseline, frozen_jobs, reduced_jobs, threshold = get_backpressure_config()

    # Check if learning is frozen due to critical instability or Hopf risk
    if governor_state.is_frozen():
        return frozen_jobs

    # Get stability margin (try parameter, then poller, then assume safe)
    S = stability_margin
    if S is None:
        S = _try_read_stability_from_poller()

    # If we can't determine S, default to safe baseline
    if S is None:
        return baseline

    # Adaptive backpressure based on stability margin
    if S < threshold:
        # Low stability: reduce parallelism
        return reduced_jobs
    else:
        # Stable: normal operation
        return baseline


def _try_read_stability_from_poller() -> float | None:
    """
    Attempt to read current stability margin from adaptive_wisdom_poller.

    Returns:
        float | None: Stability margin S, or None if unavailable
    """
    try:
        # Avoid circular import by importing locally
        import orchestrator.adaptive_wisdom_poller as poller

        # Check if poller is enabled and running
        if not poller.ENABLED:
            return None

        # Get current state snapshot
        state = poller.get_current_state()
        return state.get("S")
    except (ImportError, Exception):
        # Poller not available or not running
        return None


def get_backpressure_status() -> dict:
    """
    Get current backpressure status for monitoring/debugging.

    Returns:
        dict: Status including current max_jobs, frozen state, stability margin
    """
    baseline, frozen_jobs, reduced_jobs, threshold = get_backpressure_config()
    is_frozen = governor_state.is_frozen()
    S = _try_read_stability_from_poller()
    max_jobs = compute_max_concurrent_jobs(stability_margin=S)

    mode = "FROZEN" if is_frozen else ("REDUCED" if S and S < threshold else "BASELINE")

    return {
        "max_concurrent_jobs": max_jobs,
        "mode": mode,
        "frozen": is_frozen,
        "stability_margin": S,
        "config": {
            "baseline_jobs": baseline,
            "frozen_jobs": frozen_jobs,
            "reduced_jobs": reduced_jobs,
            "stability_threshold": threshold,
        },
    }
