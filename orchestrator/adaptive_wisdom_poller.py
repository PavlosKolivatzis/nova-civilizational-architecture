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
from collections import deque
from contextlib import contextmanager
from typing import Dict, Optional

from nova.adaptive_wisdom_core import Params3D, State3D, ThreeDProvider
from nova.bifurcation_monitor import BifurcationMonitor
from nova.governor import state as governor_state
from nova.governor.adaptive_wisdom import AdaptiveWisdomGovernor
from nova.metrics import wisdom_metrics
from nova.wisdom.generativity_core import (
    GenerativityParams,
    compute_components,
    compute_gstar,
    compute_novelty,
    eta_bias as compute_eta_bias,
)
from nova.wisdom.generativity_context import get_context, current_g0

__all__ = ["start", "stop", "get_current_state", "get_state", "get_interval"]


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


def _parse_generativity_params() -> GenerativityParams:
    """Parse generativity parameters from environment."""
    # Parse weights (α, β, γ)
    weights_raw = os.getenv("NOVA_WISDOM_G_WEIGHTS", "0.4,0.3,0.3")
    try:
        parts = [float(x.strip()) for x in weights_raw.split(",")]
        if len(parts) >= 3:
            alpha, beta, gamma = parts[0], parts[1], parts[2]
        else:
            alpha, beta, gamma = 0.4, 0.3, 0.3
    except Exception:
        alpha, beta, gamma = 0.4, 0.3, 0.3

    # Parse target and gain
    g0 = float(os.getenv("NOVA_WISDOM_G_TARGET", "0.6"))
    kappa = float(os.getenv("NOVA_WISDOM_G_KAPPA", "0.02"))

    return GenerativityParams(alpha=alpha, beta=beta, gamma=gamma, g0=g0, kappa=kappa)


def _get_generativity_gates() -> tuple[float, float]:
    """Get gating thresholds for G* bias."""
    min_s = float(os.getenv("NOVA_WISDOM_G_MIN_S", "0.03"))
    min_h = float(os.getenv("NOVA_WISDOM_G_MIN_H", "0.02"))
    return (min_s, min_h)


# Configuration
INTERVAL = _get_interval()
ENABLED = _get_enabled()

# Shared state
_stop = threading.Event()
_thread: Optional[threading.Thread] = None
_lock = threading.Lock()
# Note: eta and frozen now managed by governor_state (GovernorState singleton)
_current_state: Dict[str, float] = {
    "gamma": 0.7,
    "S": 0.05,
    "rho": 0.0,
    "H": float("inf"),
    "G": 0.0,
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
        state = dict(_current_state)
        # Add eta and frozen from GovernorState
        state["eta"] = governor_state.get_eta()
        state["frozen"] = governor_state.is_frozen()
        return state


def get_state() -> Dict[str, float]:
    """Alias for get_current_state() (for peer sync endpoint compatibility)."""
    return get_current_state()


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


def _get_peer_qualities() -> list[float]:
    """
    Attempt to read per-peer quality scores from federation metrics.

    Returns:
        list[float]: Per-peer quality scores, or empty list if unavailable
    """
    try:
        from nova.metrics.registry import REGISTRY
        from prometheus_client import REGISTRY as prom_registry

        # Try to find nova_federation_peer_quality metric
        for collector in REGISTRY._collector_to_names:
            if hasattr(collector, "_metrics"):
                for metric_name, metric in collector._metrics.items():
                    if "nova_federation_peer_quality" in str(metric_name):
                        if hasattr(metric, "_samples"):
                            return [sample[2] for sample in metric._samples() if sample[2] is not None]
        return []
    except Exception:
        return []


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

    # Generativity computation setup
    gen_params = _parse_generativity_params()
    min_s_gate, min_h_gate = _get_generativity_gates()

    # Rolling buffers for generativity computation
    # 1m window = ~4 samples at 15s interval, 5m = ~20 samples
    gamma_buffer_1m = deque(maxlen=4)
    gamma_buffer_5m = deque(maxlen=20)
    eta_buffer_1m = deque(maxlen=4)
    peer_quality_buffer_1m = deque(maxlen=4)

    while not _stop.is_set():
        try:
            # Get current state
            with _lock:
                current = State3D(
                    gamma=_current_state["gamma"],
                    S=_current_state["S"],
                    eta=governor_state.get_eta(),  # Read from GovernorState
                )
            frozen = governor_state.is_frozen()  # Read from GovernorState

            # Compute Jacobian and analyze
            jacobian = provider.jacobian(current)
            analysis = monitor.analyze(jacobian)

            # Update rolling buffers for generativity
            gamma_buffer_1m.append(current.gamma)
            gamma_buffer_5m.append(current.gamma)
            eta_buffer_1m.append(current.eta)

            # Phase 16-2: Get live peers from peer sync (if enabled)
            live_peers = []
            try:
                from orchestrator.app import _peer_store
                if _peer_store:
                    live_peers = _peer_store.get_live_peers(max_age_seconds=90)
            except (ImportError, AttributeError):
                # Peer sync not available or not started
                pass

            # Calculate Novelty from live peer diversity
            N = compute_novelty(live_peers) if live_peers else 0.0

            # Get generativity context (solo vs federated)
            context_state = get_context(len(live_peers))
            g0_target = current_g0()

            # Get peer qualities (legacy fallback for peer_quality metric)
            peer_qualities = _get_peer_qualities()
            if peer_qualities:
                peer_quality_buffer_1m.extend(peer_qualities)

            # Compute generativity components (P, Cc)
            if gamma_buffer_1m and gamma_buffer_5m:
                gamma_avg_1m = sum(gamma_buffer_1m) / len(gamma_buffer_1m)
                gamma_avg_5m = sum(gamma_buffer_5m) / len(gamma_buffer_5m)
                eta_series = list(eta_buffer_1m)

                # Compute P (Progress) and Cc (Consistency) only
                # N is now calculated from live peers above
                peer_quality_series = list(peer_quality_buffer_1m)
                P, _N_unused, Cc = compute_components(
                    gamma_avg_1m=gamma_avg_1m,
                    gamma_avg_5m=gamma_avg_5m,
                    eta_series_1m=eta_series,
                    peer_quality_series_1m=peer_quality_series,
                )
                # Use real N from live peers, not the one from compute_components
                G = compute_gstar(gen_params, P, N, Cc)
                bias = compute_eta_bias(gen_params, G)

                # Publish generativity components
                wisdom_metrics.publish_generativity_components(
                    progress=P, novelty=N, consistency=Cc, eta_bias=bias
                )
            else:
                # Insufficient data, use fallback
                G = 0.6  # Target value
                bias = 0.0
                # N is already calculated from live peers (line 237), preserve it
                P, Cc = 0.0, 0.0

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

            # Apply generativity bias (gated by stability)
            # Gate out when S < min_s or H < min_h
            if not frozen and analysis.S >= min_s_gate and analysis.H >= min_h_gate:
                new_eta += bias
                # Clamp to global bounds
                new_eta = max(eta_min, min(eta_max, new_eta))

            # Apply TRI feedback cap (optional, if enabled)
            if os.getenv("NOVA_TRI_ETA_CAP_ENABLED", "1") == "1":
                try:
                    from nova.slots.slot04_tri.wisdom_feedback import get_tri_coherence, compute_tri_eta_cap
                    coherence = get_tri_coherence()
                    if coherence is not None:
                        tri_cap = compute_tri_eta_cap(coherence)
                        new_eta = min(new_eta, tri_cap)
                except (ImportError, Exception):
                    # TRI feedback unavailable, continue without cap
                    pass

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
                _current_state["rho"] = analysis.rho
                _current_state["H"] = analysis.H
                _current_state["G"] = G
                # Phase 16-2: Store generativity components and peer info
                _current_state["g_components"] = {
                    "progress": P,
                    "novelty": N,
                    "consistency": Cc,
                }
                _current_state["g_star"] = G
                _current_state["peer_quality"] = sum(p.peer_quality for p in live_peers) / len(live_peers) if live_peers else 0.7

            # Update GovernorState (single source of truth for eta and frozen)
            governor_state.set_eta(new_eta)
            governor_state.set_frozen(new_frozen)

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
