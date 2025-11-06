"""
Environment flags for Nova configuration (Phase 16+).

Centralized configuration for feature flags and parameters that control
system behavior via environment variables.

Design:
    - Type-safe getters with defaults
    - Range validation and clamping
    - Clear documentation of valid ranges
"""

from __future__ import annotations

import os

__all__ = [
    "get_fed_mock_peers",
    "get_fed_mock_std",
]


def get_fed_mock_peers() -> int:
    """
    Get number of mock peers for offline federation testing.

    Environment Variable:
        NOVA_FED_MOCK_PEERS

    Default: 0 (disabled)
    Range: [0, 10]

    Returns:
        int: Number of mock peers to generate (0 = disabled)

    Notes:
        - 0: No mock peers, single-node operation (N = 0)
        - 1: Still single-node behavior (N = 0, need >= 2 for diversity)
        - 2-10: Multi-peer mock federation (N > 0)
    """
    peers_str = os.getenv("NOVA_FED_MOCK_PEERS", "0")
    try:
        peers = int(peers_str)
    except ValueError:
        return 0
    return max(0, min(10, peers))


def get_fed_mock_std() -> float:
    """
    Get standard deviation for mock peer generativity variance.

    Environment Variable:
        NOVA_FED_MOCK_STD

    Default: 0.15
    Range: [0.05, 0.30]

    Returns:
        float: Standard deviation for generativity distribution

    Notes:
        - Lower values (0.05-0.10): Homogeneous peer population
        - Medium values (0.15-0.20): Moderate diversity
        - Higher values (0.25-0.30): High peer variance
        - Controls Novelty (N) component magnitude
    """
    std_str = os.getenv("NOVA_FED_MOCK_STD", "0.15")
    try:
        std = float(std_str)
    except ValueError:
        return 0.15
    return max(0.05, min(0.30, std))
