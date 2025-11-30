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

# Default global weights for anomaly components
DEFAULT_W = {
    "tri_drift_z": float(os.getenv("NOVA_UNLEARN_W_TRI", "0.5")),
    "system_pressure": float(os.getenv("NOVA_UNLEARN_W_PRESS", "0.4")),
    "phase_jitter": float(os.getenv("NOVA_UNLEARN_W_JITTER", "0.1")),
}

# Backward compatibility alias
W = DEFAULT_W

# Slot-specific weight overrides (Phase 4.1: slot-specific memory metabolism)
SLOT_W = {
    # Cultural synthesis slots - higher TRI sensitivity, cultural pressure response
    "slot06": {
        "tri_drift_z": float(os.getenv("NOVA_SLOT06_W_TRI", "0.7")),      # Cultural synthesis sensitive to truth drift
        "system_pressure": float(os.getenv("NOVA_SLOT06_W_PRESS", "0.5")), # Moderate pressure response
        "phase_jitter": float(os.getenv("NOVA_SLOT06_W_JITTER", "0.1")),   # Low jitter sensitivity
    },
    # Production control slots - high pressure sensitivity, deployment feedback
    "slot07": {
        "tri_drift_z": float(os.getenv("NOVA_SLOT07_W_TRI", "0.3")),      # Lower TRI focus
        "system_pressure": float(os.getenv("NOVA_SLOT07_W_PRESS", "0.8")), # High pressure sensitivity
        "phase_jitter": float(os.getenv("NOVA_SLOT07_W_JITTER", "0.2")),   # Moderate jitter response
    },
    # Memory/truth slots - balanced TRI and pressure, low jitter
    "slot04": {  # TRI engine
        "tri_drift_z": float(os.getenv("NOVA_SLOT04_W_TRI", "0.6")),      # Moderate TRI sensitivity
        "system_pressure": float(os.getenv("NOVA_SLOT04_W_PRESS", "0.3")), # Lower pressure response
        "phase_jitter": float(os.getenv("NOVA_SLOT04_W_JITTER", "0.05")),  # Very low jitter
    },
    "slot08": {  # Memory ethics/lock
        "tri_drift_z": float(os.getenv("NOVA_SLOT08_W_TRI", "0.4")),      # Truth-aware memory
        "system_pressure": float(os.getenv("NOVA_SLOT08_W_PRESS", "0.6")), # High pressure response
        "phase_jitter": float(os.getenv("NOVA_SLOT08_W_JITTER", "0.1")),   # Low jitter sensitivity
    },
    # Deployment slots - deployment feedback loops
    "slot10": {
        "tri_drift_z": float(os.getenv("NOVA_SLOT10_W_TRI", "0.5")),      # Deployment truth validation
        "system_pressure": float(os.getenv("NOVA_SLOT10_W_PRESS", "0.7")), # High deployment pressure response
        "phase_jitter": float(os.getenv("NOVA_SLOT10_W_JITTER", "0.3")),   # Deployment jitter sensitivity
    },
}

# Internal state (thread-protected)
_lock = threading.Lock()
_ewma = {"tri_drift_z": 0.0, "system_pressure": 0.0, "phase_jitter": 0.0}
_breaches = deque(maxlen=WIN)
_engaged = False
_last_score = 0.0
_last_multiplier = 1.0


def _get_weights_for_slot(slot: Optional[str] = None) -> dict:
    """Get anomaly weights for specific slot, falling back to defaults.

    Args:
        slot: Slot identifier (e.g., "slot06", "slot07") or None for global

    Returns:
        Dict with tri_drift_z, system_pressure, phase_jitter weights
    """
    w = dict(DEFAULT_W)
    if slot and slot in SLOT_W:
        w.update(SLOT_W[slot])
    return w


def _ewma_update(key: str, value: float) -> None:
    """Update EWMA for given metric key."""
    _ewma[key] = ALPHA * value + (1.0 - ALPHA) * _ewma[key]


def _normalize(value: float, _min_val: float, max_val: float) -> float:
    """Clamp and rescale value to [0, 1] range."""
    return max(0.0, min(max_val, value)) / max(1e-9, max_val)


def update_anomaly_inputs(tri: dict, system: dict, slot: Optional[str] = None) -> None:
    """Feed raw metric readings to the anomaly detector.

    Called once per sweep interval to update internal EWMA state and
    compute engagement status based on sustained threshold breaches.

    Args:
        tri: TRI metrics dict with keys like 'drift_z', 'phase_jitter'
        system: System metrics dict with 'system_pressure_level' or 'pressure'
        slot: Target slot for Phase 4.1 slot-specific weighting (optional)
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

        # Compute weighted anomaly score with Phase 4.1 slot-specific weights
        w = _get_weights_for_slot(slot)
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


def get_dynamic_half_life(base_half_life: float = 300.0, slot: Optional[str] = None) -> float:
    """Phase 4.1: Dynamic half-life based on anomaly score and TRI state.

    Higher anomaly scores → shorter half-life (faster decay)
    Higher TRI drift → longer half-life (preserve memory during instability)

    Args:
        base_half_life: Baseline half-life in seconds (default 300.0 = 5 min)
        slot: Target slot for future slot-specific half-life curves

    Returns:
        Adjusted half-life in seconds, clamped to [60, 1800] range
    """
    if os.getenv("NOVA_UNLEARN_ANOMALY", "0") != "1":
        return base_half_life

    with _lock:
        # Phase 4.1: Experiment with dynamic TRI weighting
        tri_component = _ewma["tri_drift_z"]
        pressure_component = _ewma["system_pressure"]

        # TRI-aware adjustment: high TRI drift → preserve memory longer
        tri_multiplier = 1.0 + (tri_component * 2.0)  # [1.0, 3.0] range

        # Pressure-aware adjustment: high pressure → faster decay
        pressure_divisor = 1.0 + (pressure_component * 1.5)  # [1.0, 2.5] range

        # Combined dynamic half-life
        dynamic_half_life = base_half_life * tri_multiplier / pressure_divisor

        # Clamp to safe operational bounds
        min_half_life = float(os.getenv("NOVA_UNLEARN_MIN_HALF_LIFE", "60"))    # 1 minute
        max_half_life = float(os.getenv("NOVA_UNLEARN_MAX_HALF_LIFE", "1800"))  # 30 minutes

        return max(min_half_life, min(max_half_life, dynamic_half_life))


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
            "dynamic_half_life": get_dynamic_half_life(),  # Phase 4.1 observability
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
