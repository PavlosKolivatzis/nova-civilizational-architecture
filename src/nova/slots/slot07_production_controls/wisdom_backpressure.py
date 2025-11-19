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
import typing as _typing

from prometheus_client import Gauge as _Gauge
from nova.governor import state as governor_state
from nova.metrics.registry import REGISTRY as _REGISTRY

__all__ = ["compute_max_concurrent_jobs", "get_backpressure_config", "get_tri_signal_snapshot"]

_slot7_jobs_current = _Gauge(
    "nova_slot07_jobs_current",
    "Current Slot7 max concurrent jobs after wisdom backpressure",
    registry=_REGISTRY,
)
_slot7_jobs_reason = _Gauge(
    "nova_slot07_jobs_reason",
    "Slot7 backpressure reason code (0=baseline, 1=stability reduced, 2=frozen)",
    registry=_REGISTRY,
)

_tri_signal_snapshot: _typing.Dict[str, _typing.Any] = {}


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


def _read_tri_truth_signal() -> _typing.Dict[str, _typing.Any]:
    """Fetch latest TRI truth signal from Semantic Mirror (best-effort)."""
    global _tri_signal_snapshot
    try:
        from orchestrator.semantic_mirror import get_semantic_mirror

        mirror = get_semantic_mirror()
    except Exception:
        return _tri_signal_snapshot

    def _mirror_get(key: str, default=None):
        try:
            return mirror.get_context(key, default=default)
        except TypeError:
            try:
                return mirror.get_context(key, "slot07_production_controls")
            except TypeError:
                return default

    signal = _mirror_get("slot04.tri_truth_signal", default=None)
    if isinstance(signal, dict):
        _tri_signal_snapshot = signal
    return _tri_signal_snapshot


def get_tri_signal_snapshot() -> _typing.Dict[str, _typing.Any]:
    """Return latest cached TRI truth signal snapshot."""
    return dict(_tri_signal_snapshot)


def _decide_job_cap(stability_margin: float | None = None) -> Tuple[int, int]:
    """
    Decide Slot 7 job cap, emitting Prometheus gauges for observability.

    Args:
        stability_margin: Optional stability margin override (S). If None, reads poller state.

    Returns:
        Tuple[int, int]: (cap, reason_code)
    """
    baseline, frozen_jobs, reduced_jobs, threshold = get_backpressure_config()
    cap, reason = baseline, 0

    tri_signal = _read_tri_truth_signal()
    tri_band = (tri_signal.get("tri_band") or "").lower() if tri_signal else ""

    if governor_state.is_frozen() or tri_band == "red":
        cap, reason = frozen_jobs, 2
    else:
        S = stability_margin if stability_margin is not None else _try_read_stability_from_poller()
        if tri_signal:
            drift = tri_signal.get("tri_drift_z")
            try:
                drift = float(drift)
            except (TypeError, ValueError):
                drift = None
            if drift is not None:
                drift_threshold = float(os.getenv("NOVA_SLOT07_TRI_DRIFT_THRESHOLD", "2.2"))
                if drift >= drift_threshold:
                    threshold = max(threshold, float(os.getenv("NOVA_SLOT07_STABILITY_THRESHOLD_TRI", "0.05")))

        if S is None:
            cap, reason = baseline, 0
        elif S < threshold:
            cap, reason = reduced_jobs, 1
        else:
            cap, reason = baseline, 0

        if tri_band == "amber" and reason == 0:
            cap, reason = reduced_jobs, 1

    _slot7_jobs_current.set(cap)
    _slot7_jobs_reason.set(reason)
    return cap, reason


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
    cap, _ = _decide_job_cap(stability_margin=stability_margin)
    return cap


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


def get_backpressure_status(stability_margin: float | None = None) -> _typing.Dict[str, _typing.Any]:
    """
    Get current backpressure status for monitoring/debugging.

    Returns:
        dict: Status including current max_jobs, frozen state, stability margin
    """
    baseline, frozen_jobs, reduced_jobs, threshold = get_backpressure_config()
    observed_stability = stability_margin if stability_margin is not None else _try_read_stability_from_poller()
    max_jobs, reason = _decide_job_cap(stability_margin=observed_stability)
    tri_signal = get_tri_signal_snapshot()

    return {
        "max_concurrent_jobs": max_jobs,
        "mode": _describe_mode(max_jobs, reason, baseline, reduced_jobs, frozen_jobs),
        "frozen": governor_state.is_frozen(),
        "stability_margin": observed_stability,
        "tri_signal": tri_signal or None,
        "config": {
            "baseline_jobs": baseline,
            "frozen_jobs": frozen_jobs,
            "reduced_jobs": reduced_jobs,
            "stability_threshold": threshold,
        },
    }


def _describe_mode(
    max_jobs: int,
    reason: int,
    baseline: int,
    reduced_jobs: int,
    frozen_jobs: int,
) -> str:
    if reason == 2 or max_jobs <= frozen_jobs:
        return "FROZEN"
    if reason == 1 or max_jobs == reduced_jobs or (reason == 0 and max_jobs < baseline):
        return "REDUCED"
    return "BASELINE"


def __getattr__(name: str):
    if name == "decide_job_cap":
        def _compat_decide_job_cap(*args, **kwargs):
            cap, _ = _decide_job_cap(*args, **kwargs)
            return cap

        _compat_decide_job_cap.__name__ = "decide_job_cap"
        _compat_decide_job_cap.__doc__ = (
            "Compatibility shim returning only the job cap. "
            "Use compute_max_concurrent_jobs instead."
        )
        return _compat_decide_job_cap
    raise AttributeError(name)
