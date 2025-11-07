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

from prometheus_client import Gauge
from nova.governor import state as governor_state
from nova.metrics.registry import REGISTRY

__all__ = ["compute_max_concurrent_jobs", "decide_job_cap", "get_backpressure_config"]

_slot7_jobs_current = Gauge(
    "nova_slot07_jobs_current",
    "Current Slot7 max concurrent jobs after wisdom backpressure",
    registry=REGISTRY,
)
_slot7_jobs_reason = Gauge(
    "nova_slot07_jobs_reason",
    "Slot7 backpressure reason code (0=baseline, 1=stability reduced, 2=frozen)",
    registry=REGISTRY,
)


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


def decide_job_cap(stability_margin: float | None = None) -> int:
    """
    Decide Slot 7 job cap, emitting Prometheus gauges for observability.

    Args:
        stability_margin: Optional stability margin override (S). If None, reads poller state.

    Returns:
        int: Chosen concurrency cap.
    """
    baseline, frozen_jobs, reduced_jobs, threshold = get_backpressure_config()
    cap, reason = baseline, 0

    if governor_state.is_frozen():
        cap, reason = frozen_jobs, 2
    else:
        S = stability_margin if stability_margin is not None else _try_read_stability_from_poller()
        if S is None:
            cap, reason = baseline, 0
        elif S < threshold:
            cap, reason = reduced_jobs, 1
        else:
            cap, reason = baseline, 0

    _slot7_jobs_current.set(cap)
    _slot7_jobs_reason.set(reason)
    return cap


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
    return decide_job_cap(stability_margin=stability_margin)


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
    max_jobs = decide_job_cap(stability_margin=S)

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
