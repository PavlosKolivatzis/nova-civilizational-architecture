"""
Generativity Score (G*) Computation for Adaptive Wisdom Governor.

Generativity measures system creative output and novelty, factoring into
learning rate adjustment via a soft bias term.

Formula:
    G* = α·P + β·N + γ·Cc

Where:
    P  = Progress (recent growth in wisdom γ)
    N  = Novelty (structural change in peer landscape)
    Cc = Consistency (steadiness of learning rate η)

Controller Integration:
    Δη = κ·(G* - G₀)  [soft bias term]

    Gated out when S < 0.03 or H < 0.02 (instability)
    Applied before TRI cap and global clamps [0.05, 0.18]

Design:
    - Pure computation (no I/O)
    - Environment-tunable parameters
    - Defensive clipping to [0,1] range
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Sequence

__all__ = [
    "GenerativityParams",
    "compute_components",
    "compute_gstar",
    "compute_novelty",
    "eta_bias",
]

# Epsilon for numerical stability
EPS = 1e-9


@dataclass
class GenerativityParams:
    """Parameters for generativity computation."""

    alpha: float = 0.4  # Weight for progress component
    beta: float = 0.3  # Weight for novelty component
    gamma: float = 0.3  # Weight for consistency component
    g0: float = 0.6  # Target generativity
    kappa: float = 0.02  # Bias gain (how strongly G* affects η)


def _clip(x: float, lo: float = 0.0, hi: float = 1.0) -> float:
    """Clip value to [lo, hi] range."""
    return max(lo, min(hi, x))


def compute_novelty(peers: Sequence) -> float:
    """
    Compute Novelty (N) component from peer diversity.

    Measures structural change in peer landscape via standard deviation
    of peer generativity values.

    Args:
        peers: Sequence of PeerSummary objects with .generativity attribute

    Returns:
        float: Novelty score N ∈ [0,1]
               Returns 0.0 if < 2 peers (no diversity)

    Formula:
        N = std_dev([p.generativity for p in peers]) if len(peers) >= 2 else 0.0

    Notes:
        - Single-node deployments: N = 0 (no peer diversity)
        - Multi-peer federations: N > 0 (reflects peer variance)
        - Normalized to [0,1] range via clipping std_dev / 0.5
    """
    if len(peers) < 2:
        return 0.0

    generativities = [p.generativity for p in peers]
    mean = sum(generativities) / len(generativities)
    variance = sum((g - mean) ** 2 for g in generativities) / len(generativities)
    std_dev = math.sqrt(variance)

    # Normalize to [0,1] assuming typical std_dev ~0.15-0.25
    # Clip at 0.5 to map [0, 0.5] → [0, 1]
    return _clip(std_dev / 0.5)


def compute_components(
    gamma_avg_1m: float,
    gamma_avg_5m: float,
    eta_series_1m: Sequence[float],
    peer_quality_series_1m: Sequence[float],
) -> tuple[float, float, float]:
    """
    Compute the three generativity components: Progress, Novelty, Consistency.

    Args:
        gamma_avg_1m: Average wisdom over last 1 minute
        gamma_avg_5m: Average wisdom over last 5 minutes
        eta_series_1m: Learning rate samples from last 1 minute
        peer_quality_series_1m: Per-peer quality scores from last 1 minute

    Returns:
        tuple[float, float, float]: (P, N, Cc) ∈ [0,1]³

    Formulas:
        P = clip((γ̄_1m - γ̄_5m) / max(γ̄_5m, ε), 0, 1)
        N = clip(std_peers(q)_1m / 0.5, 0, 1)
        Cc = 1 - clip(std(η)_1m / max(η̄_1m, ε), 0, 1)
    """
    # Progress: recent growth in wisdom γ
    denom = max(gamma_avg_5m, EPS)
    P = _clip((gamma_avg_1m - gamma_avg_5m) / denom)

    # Novelty: spread across peers (structural change)
    if peer_quality_series_1m:
        mu = sum(peer_quality_series_1m) / len(peer_quality_series_1m)
        var = sum((x - mu) ** 2 for x in peer_quality_series_1m) / len(
            peer_quality_series_1m
        )
        std_peers = math.sqrt(var)
    else:
        std_peers = 0.0
    N = _clip(std_peers / 0.5)

    # Consistency: lower η variability → higher consistency
    if eta_series_1m:
        mu_eta = sum(eta_series_1m) / len(eta_series_1m)
        var_eta = sum((x - mu_eta) ** 2 for x in eta_series_1m) / len(eta_series_1m)
        std_eta = math.sqrt(var_eta)
        cv = std_eta / max(mu_eta, EPS)
    else:
        cv = 0.0
    Cc = _clip(1.0 - _clip(cv, 0.0, 1.0))

    return P, N, Cc


def compute_gstar(
    params: GenerativityParams, P: float, N: float, Cc: float
) -> float:
    """
    Compute generativity score G* from components.

    Args:
        params: Generativity parameters (weights)
        P: Progress component [0,1]
        N: Novelty component [0,1]
        Cc: Consistency component [0,1]

    Returns:
        float: G* ∈ [0,1]

    Formula:
        G* = α·P + β·N + γ·Cc
    """
    return _clip(params.alpha * P + params.beta * N + params.gamma * Cc)


def eta_bias(params: GenerativityParams, gstar: float) -> float:
    """
    Compute learning rate bias from generativity score.

    This is the soft bias term added to η in the controller:
        Δη = κ·(G* - G₀)

    Args:
        params: Generativity parameters
        gstar: Current generativity score [0,1]

    Returns:
        float: Bias term Δη (can be positive or negative)

    Notes:
        - Positive when G* > G₀ (system is creative → increase learning)
        - Negative when G* < G₀ (system stagnant → decrease learning)
        - Gated out by poller when S < 0.03 or H < 0.02
    """
    return params.kappa * (gstar - params.g0)
