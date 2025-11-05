"""
GovernorState — Single source of truth for adaptive learning rate η.

This module provides thread-safe access to the current learning rate and frozen state.
Training loops MUST read η from here, and the adaptive_wisdom_poller writes to it.

Design:
- Global singleton pattern (MODULE_STATE)
- Thread-safe read/write via Lock
- Immutable return values (defensive copies)
- Zero dependencies on slots or orchestrator

Usage (training loop):
    from nova.governor.state import get_training_eta
    eta = get_training_eta()  # Always use this, never hardcode η

Usage (poller):
    from nova.governor.state import set_eta, set_frozen
    set_eta(0.12)
    set_frozen(True)  # Freeze learning when unstable
"""

from __future__ import annotations

import threading
from dataclasses import dataclass
from typing import Tuple

__all__ = [
    "GovernorState",
    "get_training_eta",
    "get_eta",
    "set_eta",
    "is_frozen",
    "set_frozen",
    "get_state",
    "reset_for_tests",
]


@dataclass
class GovernorState:
    """Thread-safe container for governor operational state."""

    eta: float = 0.10
    frozen: bool = False


# --- Global State (Singleton) ---

_lock = threading.Lock()
_state = GovernorState()


# --- Public API ---


def get_training_eta() -> float:
    """
    Get current learning rate for training loops.

    This is the PRIMARY hook for Slot 7 / training code.
    ALWAYS use this instead of hardcoding η values.

    Returns:
        float: Current learning rate (0.0 if frozen)
    """
    with _lock:
        if _state.frozen:
            return 0.0
        return _state.eta


def get_eta() -> float:
    """
    Get current learning rate η (raw value, ignores frozen state).

    For monitoring/metrics. Training loops should use get_training_eta().
    """
    with _lock:
        return _state.eta


def set_eta(value: float) -> None:
    """
    Set learning rate η.

    Called by adaptive_wisdom_poller after bifurcation analysis.

    Args:
        value: New learning rate (should be in [eta_min, eta_max])
    """
    with _lock:
        _state.eta = float(value)


def is_frozen() -> bool:
    """Check if learning is currently frozen due to instability."""
    with _lock:
        return _state.frozen


def set_frozen(frozen: bool) -> None:
    """
    Set frozen state.

    When frozen=True, get_training_eta() returns 0.0 to halt learning.
    Called by adaptive_wisdom_poller when Hopf risk detected or S < critical.

    Args:
        frozen: True to freeze learning, False to resume
    """
    with _lock:
        _state.frozen = bool(frozen)


def get_state() -> Tuple[float, bool]:
    """
    Get complete state atomically.

    Returns:
        Tuple[float, bool]: (eta, frozen)
    """
    with _lock:
        return (_state.eta, _state.frozen)


def reset_for_tests(eta: float = 0.10, frozen: bool = False) -> None:
    """
    Reset state to defaults (for testing only).

    Args:
        eta: Initial learning rate
        frozen: Initial frozen state
    """
    with _lock:
        _state.eta = float(eta)
        _state.frozen = bool(frozen)


# --- Module-level convenience (for tests/debugging) ---

MODULE_STATE = _state  # Read-only reference for inspection (NOT for mutation!)
