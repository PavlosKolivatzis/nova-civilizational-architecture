"""
Generativity Context Auto-Switch (Phase 16-2).

Manages automatic switching between "solo" and "federated" contexts based on
live peer availability, with hysteresis to prevent flapping.

Context Modes:
- solo: Single-node operation, G* capped at ~0.30 (P≈0, N=0, Cc≈1.0), G₀=0.30
- federated: Multi-peer operation, G* can reach ≥0.55 with N>0, G₀=0.60
- auto: Automatically switch based on peer count with hysteresis

Design:
- Hysteresis: delay before switching back to solo after losing peers
- Minimum peer threshold: require N peers for federated context
- State tracking: record last time federated mode was active
- Metrics: expose context state as gauge (0=solo, 1=federated)
"""

from __future__ import annotations

import os
import time
from enum import Enum
from typing import Literal

__all__ = ["GenerativityContext", "get_context", "current_g0"]


class ContextState(Enum):
    """Generativity context states."""
    SOLO = "solo"
    FEDERATED = "federated"


class GenerativityContext:
    """
    Manages generativity context with auto-switch and hysteresis.

    Context determines G₀ target:
    - solo: G₀ = 0.30 (single-node baseline)
    - federated: G₀ = 0.60 (multi-peer target)
    """

    def __init__(self):
        """Initialize context manager."""
        # Configuration from environment
        self._mode = os.getenv("NOVA_WISDOM_G_CONTEXT", "auto").lower()
        self._hysteresis_sec = float(os.getenv("NOVA_WISDOM_G_HYSTERESIS_SEC", "120"))
        self._min_peers = int(os.getenv("NOVA_WISDOM_G_MIN_PEERS", "1"))

        # State tracking
        self._current_state = ContextState.SOLO
        self._last_fed_seen: float = 0.0  # Last time we had enough peers

    def get_context(self, live_peer_count: int, now: float | None = None) -> ContextState:
        """
        Get current context based on live peer count.

        Args:
            live_peer_count: Number of currently live peers
            now: Current timestamp (for testing), default: time.time()

        Returns:
            ContextState (SOLO or FEDERATED)

        Logic:
            - If mode="solo" or "federated": return fixed state
            - If mode="auto":
                - If live_peer_count >= min_peers: state=FEDERATED, record time
                - Else if (now - last_fed_seen) >= hysteresis: state=SOLO
                - Else: maintain current state (hysteresis delay)
        """
        if now is None:
            now = time.time()

        # Fixed modes
        if self._mode == "solo":
            return ContextState.SOLO
        if self._mode == "federated":
            return ContextState.FEDERATED

        # Auto mode with hysteresis
        if self._mode == "auto":
            if live_peer_count >= self._min_peers:
                # Have enough peers: enter/stay in federated
                self._current_state = ContextState.FEDERATED
                self._last_fed_seen = now
            else:
                # Lost peers: check hysteresis before switching to solo
                elapsed_since_fed = now - self._last_fed_seen
                if elapsed_since_fed >= self._hysteresis_sec:
                    self._current_state = ContextState.SOLO

        return self._current_state

    def current_g0(self) -> float:
        """
        Get current G₀ target based on context.

        Returns:
            float: 0.30 for solo, 0.60 for federated
        """
        return 0.60 if self._current_state == ContextState.FEDERATED else 0.30

    def get_state(self) -> ContextState:
        """Get current context state without update."""
        return self._current_state

    def reset(self) -> None:
        """Reset context to initial state (for testing)."""
        self._current_state = ContextState.SOLO
        self._last_fed_seen = 0.0


# -------------------------------------------------------------------------
# Module-level singleton
# -------------------------------------------------------------------------

_context_manager: GenerativityContext | None = None


def get_context(live_peer_count: int, now: float | None = None) -> ContextState:
    """
    Get current generativity context.

    Args:
        live_peer_count: Number of live peers
        now: Current timestamp (for testing)

    Returns:
        ContextState (SOLO or FEDERATED)
    """
    global _context_manager
    if _context_manager is None:
        _context_manager = GenerativityContext()
    return _context_manager.get_context(live_peer_count, now)


def current_g0() -> float:
    """
    Get current G₀ target based on active context.

    Returns:
        float: 0.30 (solo) or 0.60 (federated)
    """
    global _context_manager
    if _context_manager is None:
        _context_manager = GenerativityContext()
    return _context_manager.current_g0()
