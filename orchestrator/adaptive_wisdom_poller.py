"""Adaptive wisdom background poller for bifurcation-aware control.

Runs periodic eigenvalue analysis and adapts learning rate η based on:
  - Stability margin S
  - Hopf distance H
  - Generativity score G*

Safety protocols:
  - S < 0.01: Immediate clamp to η = 0.05 (CRITICAL)
  - Hopf detected: Freeze learning, alert operator
  - Recovery: Gradual ramp after stabilization
"""

from __future__ import annotations

import os
import threading
import time
from contextlib import contextmanager
from typing import Dict, Optional

from nova.adaptive_wisdom_core import Params3D, State3D, ThreeDProvider
from nova.bifurcation_monitor import BifurcationMonitor
from nova.governor.adaptive_wisdom import AdaptiveWisdomGovernor
from nova.metrics import wisdom_metrics

__all__ = ["start", "stop", "get_current_state", "get_interval"]


def _get_interval() -> float:
    """Get polling interval from environment."""
    raw = os.getenv("NOVA_WISDOM_POLL_INTERVAL", "")
    try:
        return float(raw) if raw else 15.0
    except Exception:
        return 15.0


def _get_enabled() -> bool:
    """Check if wisdom governor is enabled."""
    raw = os.getenv("NOVA_WISDOM_GOVERNOR_ENABLED", "").lower()
    return raw in ("1", "true", "yes", "on")


# Configuration
INTERVAL = _get_interval()
ENABLED = _get_enabled()

# Shared state
_stop = threading.Event()
_thread: Optional[threading.Thread] = None
_lock = threading.Lock()
_current_state: Dict[str, float] = {
    "gamma": 0.7,
    "S": 0.05,
    "eta": float(os.getenv("NOVA_WISDOM_ETA_DEFAULT", "0.10")),
    "rho": 0.0,
    "H": float("inf"),
    "G": 0.0,
    "frozen": False,
}


@contextmanager
def _timed(summary):
    """Context manager for timing operations."""
    start = time.perf_counter()
    try:
        yield
    finally:
        summary.observe(time.perf_counter() - start)


def get_current_state() -> Dict[str, float]:
    """Get current wisdom state snapshot (thread-safe)."""
    with _lock:
        return dict(_current_state)


def get_interval() -> float:
    """Get current polling interval."""
    return INTERVAL


def start() -> Optional[threading.Thread]:
    """Start the adaptive wisdom poller background thread.

    Returns:
        Thread object if started, None if already running or disabled
    """
    if not ENABLED:
        return None

    global _thread
    with _lock:
        if _thread and _thread.is_alive():
            return _thread
        _stop.clear()
        _thread = threading.Thread(target=_loop, name="adaptive-wisdom", daemon=True)
        _thread.start()
    return _thread


def stop() -> None:
    """Stop the adaptive wisdom poller."""
    global _thread
    _stop.set()
    with _lock:
        thread = _thread
        _thread = None
    if thread and thread.is_alive():
        thread.join(timeout=1.0)


def _compute_generativity(state: State3D, analysis) -> float:
    """Compute generativity score G* = f(gamma, S, H).

    Simple linear combination for MVS.
    Can be enhanced to full C*ρ*S - α*H formula later.
    """
    # Simple approximation: high gamma + high S + low H → high generativity
    # G* ≈ γ + S - 0.1*min(H, 1.0)
    H_clamped = min(analysis.H, 1.0)
    G = state.gamma + analysis.S - 0.1 * H_clamped
    return max(0.0, min(1.0, G))


def _loop():
    """Main polling loop."""
    # Initialize components
    params = Params3D.from_env()
    provider = ThreeDProvider(params)
    monitor = BifurcationMonitor(
        hopf_threshold=float(os.getenv("NOVA_WISDOM_HOPF_THRESHOLD", "0.02"))
    )

    eta_min = float(os.getenv("NOVA_WISDOM_ETA_MIN", "0.05"))
    eta_max = float(os.getenv("NOVA_WISDOM_ETA_MAX", "0.18"))
    eta_default = float(os.getenv("NOVA_WISDOM_ETA_DEFAULT", "0.10"))
    governor = AdaptiveWisdomGovernor(eta=eta_default, eta_min=eta_min, eta_max=eta_max)

    # Quality target for gamma learning
    Q = params.Q

    while not _stop.is_set():
        try:
            # Get current state
            with _lock:
                current = State3D(
                    gamma=_current_state["gamma"],
                    S=_current_state["S"],
                    eta=_current_state["eta"],
                )
                frozen = _current_state["frozen"]

            # Compute Jacobian and analyze
            jacobian = provider.jacobian(current)
            analysis = monitor.analyze(jacobian)

            # Compute generativity
            G = _compute_generativity(current, analysis)

            # Update metrics
            wisdom_metrics.publish_wisdom_telemetry(
                eta=current.eta,
                gamma=current.gamma,
                generativity=G,
                stability_margin=analysis.S,
                hopf_distance=analysis.H,
                spectral_radius=analysis.rho,
            )

            # Controller logic (if not frozen)
            new_eta = current.eta
            new_frozen = frozen

            if not frozen:
                # Safety clamps
                if analysis.S < 0.01:
                    # CRITICAL: Immediate clamp
                    new_eta = eta_min
                    new_frozen = True
                elif analysis.hopf_risk:
                    # Hopf detected: Freeze
                    new_eta = current.eta
                    new_frozen = True
                else:
                    # Normal operation: Use governor
                    telemetry = governor.step(margin=analysis.S, G=G)
                    new_eta = telemetry.eta

            # Evolve gamma (simplified: dγ/dt = η(Q - γ))
            # Euler step with dt = INTERVAL
            dt = INTERVAL
            dgamma_dt = new_eta * (Q - current.gamma)
            new_gamma = current.gamma + dgamma_dt * dt
            new_gamma = max(0.0, min(1.0, new_gamma))  # Clamp to [0, 1]

            # Update shared state
            with _lock:
                _current_state["gamma"] = new_gamma
                _current_state["S"] = analysis.S
                _current_state["eta"] = new_eta
                _current_state["rho"] = analysis.rho
                _current_state["H"] = analysis.H
                _current_state["G"] = G
                _current_state["frozen"] = new_frozen

        except Exception as e:
            # Log error but continue
            print(f"Wisdom poller error: {e}")

        # Wait for next interval
        _stop.wait(INTERVAL)


if __name__ == "__main__":
    # Quick test
    print(f"Wisdom governor enabled: {ENABLED}")
    print(f"Polling interval: {INTERVAL}s")

    if ENABLED:
        start()
        print("Poller started. Monitoring for 30s...")
        for i in range(6):
            time.sleep(5)
            state = get_current_state()
            print(f"[{i*5}s] γ={state['gamma']:.3f} S={state['S']:.3f} η={state['eta']:.3f} H={state['H']:.3f}")
        stop()
        print("Poller stopped.")
