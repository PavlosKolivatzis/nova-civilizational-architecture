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
from nova.orchestrator.thresholds.manager import get_threshold, snapshot_thresholds

try:  # pragma: no cover - semantic mirror not always available in tests
    from nova.orchestrator.semantic_mirror import publish as _publish_context
except Exception:  # pragma: no cover
    _publish_context = None

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
    try:
        threshold = get_threshold("slot07_stability_threshold")
    except KeyError:
        threshold = float(os.getenv("NOVA_SLOT07_STABILITY_THRESHOLD", "0.03"))

    # Safety: ensure frozen < reduced < baseline
    frozen = max(1, min(frozen, baseline // 2))
    reduced = max(frozen + 1, min(reduced, baseline - 1))

    return (baseline, frozen, reduced, threshold)


def _read_tri_truth_signal() -> _typing.Dict[str, _typing.Any]:
    """Fetch latest TRI truth signal from Semantic Mirror (best-effort)."""
    global _tri_signal_snapshot
    try:
        from nova.orchestrator.semantic_mirror import get_semantic_mirror

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


def _as_float(value: _typing.Any) -> float | None:
    try:
        if value is None:
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def _publish_backpressure_context(payload: dict) -> None:
    """Publish backpressure diagnostics to Semantic Mirror."""
    if not _publish_context:
        return
    try:
        _publish_context(
            "slot07.backpressure_state",
            payload,
            "slot07_production_controls",
            ttl=180.0,
        )
    except Exception:
        return


def _decide_job_cap(stability_margin: float | None = None) -> Tuple[int, int]:
    """
    Decide Slot 7 job cap, emitting Prometheus gauges for observability.

    Args:
        stability_margin: Optional stability margin override (S). If None, reads poller state.

    Returns:
        Tuple[int, int]: (cap, reason_code)
    """
    baseline, frozen_jobs, reduced_jobs, stability_threshold = get_backpressure_config()
    thresholds = snapshot_thresholds()
    tri_drift_threshold = thresholds.get("slot07_tri_drift_threshold", 2.2)
    stability_freeze_threshold = thresholds.get("slot07_stability_threshold_tri", 0.05)
    tri_min_coherence = thresholds.get("tri_min_coherence", 0.65)

    tri_signal = _read_tri_truth_signal()
    tri_band = (tri_signal.get("tri_band") or "").lower() if tri_signal else ""
    tri_coherence = _as_float(tri_signal.get("tri_coherence")) if tri_signal else None
    tri_drift = _as_float(tri_signal.get("tri_drift_z")) if tri_signal else None

    observed_stability = stability_margin if stability_margin is not None else _try_read_stability_from_poller()

    if governor_state.is_frozen() or tri_band == "red" or (
        observed_stability is not None and observed_stability < stability_freeze_threshold
    ):
        cap, reason = frozen_jobs, 2
    else:
        reduce = False
        if tri_drift is not None and tri_drift >= tri_drift_threshold:
            reduce = True
        if tri_band == "amber":
            reduce = True
        if tri_coherence is not None and tri_coherence < tri_min_coherence:
            reduce = True
        if observed_stability is not None and observed_stability < stability_threshold:
            reduce = True

        cap, reason = (reduced_jobs, 1) if reduce else (baseline, 0)

    _slot7_jobs_current.set(cap)
    _slot7_jobs_reason.set(reason)
    _publish_backpressure_context(
        {
            "cap": cap,
            "reason": reason,
            "baseline": baseline,
            "reduced_jobs": reduced_jobs,
            "frozen_jobs": frozen_jobs,
            "stability_margin": observed_stability,
            "tri_signal": tri_signal or None,
            "thresholds": {
                "slot07_stability_threshold": stability_threshold,
                "slot07_stability_threshold_tri": stability_freeze_threshold,
                "slot07_tri_drift_threshold": tri_drift_threshold,
                "tri_min_coherence": tri_min_coherence,
            },
        }
    )
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
        import nova.orchestrator.adaptive_wisdom_poller as poller

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
    baseline, frozen_jobs, reduced_jobs, stability_threshold = get_backpressure_config()
    thresholds = snapshot_thresholds()
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
            "stability_threshold": stability_threshold,
            "thresholds": {
                "slot07_stability_threshold": thresholds.get("slot07_stability_threshold"),
                "slot07_stability_threshold_tri": thresholds.get("slot07_stability_threshold_tri"),
                "slot07_tri_drift_threshold": thresholds.get("slot07_tri_drift_threshold"),
                "tri_min_coherence": thresholds.get("tri_min_coherence"),
            },
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
