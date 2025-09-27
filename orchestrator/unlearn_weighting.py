"""Anomaly-aware pulse weighting for Nova's Reciprocal Contextual Unlearning.

This module implements EWMA-smoothed anomaly detection with hysteresis to
provide intelligent pulse weight multipliers. When TRI drift, system pressure,
or phase jitter indicate system stress, pulse weights are increased to
accelerate contextual unlearning where it matters most.

Design principles:
- Global scoring initially (slot-aware API for future extension)
- EWMA smoothing prevents spike-driven thrashing
- Hysteresis requires sustained breaches for engagement/disengagement
- Bounded multipliers maintain system stability
- Thread-safe for concurrent access from sweeper and receivers
"""

from collections import deque
import math
import os
import threading
from typing import Optional

# --- Configuration (environment-overridable) ---
ALPHA = float(os.getenv("NOVA_UNLEARN_ANOM_ALPHA", "0.30"))    # EWMA smoothing factor
TAU = float(os.getenv("NOVA_UNLEARN_ANOM_TAU", "1.00"))        # engagement threshold
MARGIN = float(os.getenv("NOVA_UNLEARN_ANOM_MARGIN", "0.20"))  # hysteresis margin
GAIN = float(os.getenv("NOVA_UNLEARN_ANOM_GAIN", "0.50"))      # linear gain above threshold
CAP = float(os.getenv("NOVA_UNLEARN_ANOM_CAP", "3.00"))        # maximum multiplier
WIN = int(os.getenv("NOVA_UNLEARN_ANOM_WIN", "5"))             # sliding window size
REQ = int(os.getenv("NOVA_UNLEARN_ANOM_REQ", "3"))             # required breaches for engagement

# Global weights for anomaly components
W = {
    "tri_drift_z": float(os.getenv("NOVA_UNLEARN_W_TRI", "0.5")),
    "system_pressure": float(os.getenv("NOVA_UNLEARN_W_PRESS", "0.4")),
    "phase_jitter": float(os.getenv("NOVA_UNLEARN_W_JITTER", "0.1")),
}

# Slot-specific weight overrides (empty initially, reserved for Phase 4.1)
SLOT_W = {}

# Internal state (thread-protected)
_lock = threading.Lock()
_ewma = {"tri_drift_z": 0.0, "system_pressure": 0.0, "phase_jitter": 0.0}
_breaches = deque(maxlen=WIN)
_engaged = False
_last_score = 0.0
_last_multiplier = 1.0


def _ewma_update(key: str, value: float) -> None:
    """Update EWMA for given metric key."""
    _ewma[key] = ALPHA * value + (1.0 - ALPHA) * _ewma[key]


def _normalize(value: float, min_val: float, max_val: float) -> float:
    """Clamp and rescale value to [0, 1] range."""
    return max(0.0, min(max_val, value)) / max(1e-9, max_val)


def update_anomaly_inputs(tri: dict, system: dict) -> None:
    """Feed raw metric readings to the anomaly detector.

    Called once per sweep interval to update internal EWMA state and
    compute engagement status based on sustained threshold breaches.

    Args:
        tri: TRI metrics dict with keys like 'drift_z', 'phase_jitter'
        system: System metrics dict with 'system_pressure_level' or 'pressure'
    """
    # Extract and normalize inputs
    z_score = float(tri.get("drift_z", tri.get("tri_drift_z", 0.0)))
    jitter = float(tri.get("phase_jitter", 0.0))
    pressure = float(system.get("system_pressure_level", system.get("pressure", 0.0)))

    with _lock:
        # Update EWMAs with normalized values
        _ewma_update("tri_drift_z", _normalize(z_score, 0.0, 3.0))      # cap z-score at 3σ
        _ewma_update("phase_jitter", _normalize(jitter, 0.0, 0.5))      # 0.5 as "high jitter"
        _ewma_update("system_pressure", _normalize(pressure, 0.0, 1.0))  # already normalized

        # Compute weighted anomaly score
        w = W  # use global weights (slot-specific overrides in Phase 4.1)
        score = (w["tri_drift_z"] * _ewma["tri_drift_z"] +
                w["system_pressure"] * _ewma["system_pressure"] +
                w["phase_jitter"] * _ewma["phase_jitter"])

        # Update breach tracking
        _breaches.append(score > TAU)

        global _engaged, _last_score, _last_multiplier
        _last_score = score

        # Hysteresis logic: engage if ≥REQ/WIN breaches, disengage below TAU-MARGIN
        if _engaged:
            if score < (TAU - MARGIN) and sum(_breaches) <= (REQ - 1):
                _engaged = False
        else:
            if sum(_breaches) >= REQ:
                _engaged = True

        # Compute multiplier: linear gain above threshold when engaged
        raw_multiplier = 1.0 + GAIN * max(0.0, score - TAU)
        _last_multiplier = min(CAP, max(1.0, raw_multiplier)) if _engaged else 1.0


def get_anomaly_multiplier(slot: Optional[str] = None) -> float:
    """Get current anomaly weight multiplier for pulse processing.

    Args:
        slot: Target slot name (reserved for Phase 4.1 slot-specific weights)

    Returns:
        Weight multiplier (1.0 = no adjustment, >1.0 = increased pulse weight)
    """
    if os.getenv("NOVA_UNLEARN_ANOMALY", "0") != "1":
        return 1.0

    with _lock:
        return float(_last_multiplier)


def get_anomaly_observability() -> dict:
    """Get current anomaly detection state for metrics export.

    Returns:
        Dict with score, engaged status, multiplier, and component EWMAs
    """
    with _lock:
        return {
            "score": _last_score,
            "engaged": 1.0 if _engaged else 0.0,
            "multiplier": _last_multiplier,
            "ewma_tri": _ewma["tri_drift_z"],
            "ewma_pressure": _ewma["system_pressure"],
            "ewma_jitter": _ewma["phase_jitter"],
            "breach_count": sum(_breaches),
            "breach_ratio": sum(_breaches) / max(1, len(_breaches)),
        }


def reset_anomaly_state() -> None:
    """Reset internal state (for testing)."""
    with _lock:
        global _engaged, _last_score, _last_multiplier
        _ewma.update({"tri_drift_z": 0.0, "system_pressure": 0.0, "phase_jitter": 0.0})
        _breaches.clear()
        _engaged = False
        _last_score = 0.0
        _last_multiplier = 1.0


__all__ = [
    "update_anomaly_inputs",
    "get_anomaly_multiplier",
    "get_anomaly_observability",
    "reset_anomaly_state",
]