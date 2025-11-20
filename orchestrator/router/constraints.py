from __future__ import annotations

import logging
from typing import Any, Dict, Optional

from orchestrator.router.decision import ConstraintResult

try:  # pragma: no cover - semantic mirror optional in some environments
    from orchestrator.semantic_mirror import get_semantic_mirror
except Exception:  # pragma: no cover
    get_semantic_mirror = None  # type: ignore[assignment]

try:
    from orchestrator.thresholds.manager import snapshot_thresholds
except Exception:  # pragma: no cover
    snapshot_thresholds = None  # type: ignore[assignment]

logger = logging.getLogger(__name__)


def _read_semantic_context(key: str, default: Any = None) -> Any:
    if not get_semantic_mirror:
        return default
    try:
        mirror = get_semantic_mirror()
    except Exception:
        return default
    if not mirror:
        return default
    try:
        return mirror.get_context(key, "router")
    except TypeError:
        try:
            return mirror.get_context(key, default)
        except Exception:
            return default
    except Exception:
        return default


def _current_thresholds() -> Dict[str, float]:
    if not snapshot_thresholds:
        return {}
    try:
        return snapshot_thresholds()
    except Exception:
        return {}


def _tri_signal_from_request(request_context: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    if request_context and "tri_signal" in request_context:
        raw = request_context["tri_signal"]
        if isinstance(raw, dict):
            return raw
    tri = _read_semantic_context("slot04.tri_truth_signal", default=None)
    if isinstance(tri, dict):
        return tri
    # Legacy fallbacks
    coherence = _read_semantic_context("slot04.coherence", default=None)
    drift = _read_semantic_context("slot04.tri_drift", default=None)
    jitter = _read_semantic_context("slot04.phase_jitter", default=None)
    result: Dict[str, Any] = {}
    if coherence is not None:
        result["tri_coherence"] = coherence
    if drift is not None:
        result["tri_drift_z"] = drift
    if jitter is not None:
        result["tri_jitter"] = jitter
    return result


def _slot07_state(request_context: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    if request_context and "slot07" in request_context:
        raw = request_context["slot07"]
        if isinstance(raw, dict):
            return raw
    state = _read_semantic_context("slot07.backpressure_state", default=None)
    if isinstance(state, dict):
        return state
    return {}


def _slot10_state(request_context: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    if request_context and "slot10" in request_context:
        raw = request_context["slot10"]
        if isinstance(raw, dict):
            return raw
    state = _read_semantic_context("slot10.lightclock_gate", default=None)
    if isinstance(state, dict):
        return state
    return {}


def evaluate_constraints(request_context: Optional[Dict[str, Any]] = None) -> ConstraintResult:
    """Evaluate hard routing constraints and return a deterministic result."""
    thresholds = _current_thresholds()
    tri_signal = _tri_signal_from_request(request_context)
    slot07 = _slot07_state(request_context)
    slot10 = _slot10_state(request_context)

    allowed = True
    reasons = []
    snapshot = {
        "tri_signal": tri_signal,
        "slot07": slot07,
        "slot10": slot10,
        "thresholds": thresholds,
    }

    tri_coherence = tri_signal.get("tri_coherence")
    tri_drift = tri_signal.get("tri_drift_z")
    tri_jitter = tri_signal.get("tri_jitter")

    min_coherence = thresholds.get("tri_min_coherence", 0.65)
    drift_threshold = thresholds.get("slot07_tri_drift_threshold", 2.2)
    jitter_threshold = thresholds.get("tri_max_jitter", 0.30)

    if tri_coherence is not None:
        try:
            if float(tri_coherence) < float(min_coherence):
                allowed = False
                reasons.append(f"tri_coherence<{min_coherence}")
        except (TypeError, ValueError):
            pass

    if tri_drift is not None:
        try:
            if abs(float(tri_drift)) > float(drift_threshold):
                allowed = False
                reasons.append(f"tri_drift>{drift_threshold}")
        except (TypeError, ValueError):
            pass

    if tri_jitter is not None:
        try:
            if float(tri_jitter) > float(jitter_threshold):
                allowed = False
                reasons.append(f"tri_jitter>{jitter_threshold}")
        except (TypeError, ValueError):
            pass

    slot07_mode = str(slot07.get("mode", "")).upper()
    if slot07_mode == "FROZEN" or slot07.get("reason") == 2:
        allowed = False
        reasons.append("slot07_frozen")

    slot10_gate = slot10.get("passed")
    if slot10_gate is False:
        allowed = False
        failed_reason = slot10.get("reason") or "slot10_gate_fail"
        reasons.append(str(failed_reason))

    return ConstraintResult(allowed=allowed, reasons=reasons, snapshot=snapshot)
