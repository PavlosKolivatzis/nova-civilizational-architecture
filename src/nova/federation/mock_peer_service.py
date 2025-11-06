"""
Mock Peer Service for offline federation testing (Phase 16-1).

Generates synthetic peer populations with configurable variance to enable
Novelty (N) component testing without requiring live federation.

Design:
    - Deterministic seed support for reproducibility
    - Environment-tunable variance (NOVA_FED_MOCK_STD)
    - UUIDv7 peer IDs for timestamp ordering
    - Bounded random ranges for quality/stability/generativity
"""

from __future__ import annotations

import math
import os
import random
import uuid
from typing import List

from nova.ledger.id_gen import generate_record_id
from nova.federation.schemas import PeerSummary

__all__ = ["MockPeerService"]


class MockPeerService:
    """
    Mock peer service for federation testing.

    Generates synthetic peer populations with controlled variance
    to test Novelty (N) component without live federation.
    """

    def __init__(self, seed: int | None = None):
        """
        Initialize mock peer service.

        Args:
            seed: Optional random seed for deterministic generation
        """
        self._rng = random.Random(seed)
        self._seed = seed
        self._last_peers: List[PeerSummary] = []

        # Get variance parameter from environment
        self._std = self._get_std_from_env()

    def _get_std_from_env(self) -> float:
        """
        Get standard deviation parameter from environment.

        Returns:
            float: Standard deviation clamped to [0.05, 0.30]
        """
        std_str = os.getenv("NOVA_FED_MOCK_STD", "0.15")
        try:
            std = float(std_str)
        except ValueError:
            std = 0.15
        return max(0.05, min(0.30, std))

    def generate_peers(self, count: int) -> List[PeerSummary]:
        """
        Generate synthetic peer population.

        Args:
            count: Number of peers to generate (1-10)

        Returns:
            List[PeerSummary]: Generated peer summaries

        Peer Attributes:
            - peer_id: UUIDv7 (time-sortable)
            - peer_quality: Uniform [0.4, 0.9]
            - stability_margin: Uniform [0.02, 0.05]
            - generativity: Normal(μ=0.45, σ=NOVA_FED_MOCK_STD), clipped to [0.2, 0.7]
        """
        if count < 1 or count > 10:
            raise ValueError(f"peer count must be in [1, 10], got {count}")

        peers = []
        for i in range(count):
            # Generate peer ID
            # - Deterministic UUID4 from seed if seed provided (for testing)
            # - UUIDv7 (time-sortable) if no seed (production)
            if self._seed is not None:
                # Deterministic: use seed + index to generate consistent UUID4
                namespace = uuid.UUID('00000000-0000-0000-0000-000000000000')
                name = f"mock_peer_{self._seed}_{i}"
                peer_id = str(uuid.uuid5(namespace, name))
            else:
                peer_id = generate_record_id()

            # Quality: uniform [0.4, 0.9]
            peer_quality = self._rng.uniform(0.4, 0.9)

            # Stability: uniform [0.02, 0.05]
            stability_margin = self._rng.uniform(0.02, 0.05)

            # Generativity: normal distribution with controlled std
            # Center at 0.45, clip to [0.2, 0.7]
            generativity = self._rng.normalvariate(0.45, self._std)
            generativity = max(0.2, min(0.7, generativity))

            peer = PeerSummary(
                peer_id=peer_id,
                peer_quality=peer_quality,
                stability_margin=stability_margin,
                generativity=generativity,
            )
            peers.append(peer)

        self._last_peers = peers
        return peers

    def get_peer_variance(self) -> float:
        """
        Compute variance of peer generativity values.

        This is the Novelty (N) component: measures diversity in
        peer creative output.

        Returns:
            float: Standard deviation of peer generativity values.
                   Returns 0.0 if < 2 peers.

        Formula:
            N = std_dev([p.generativity for p in peers])
        """
        if len(self._last_peers) < 2:
            return 0.0

        generativities = [p.generativity for p in self._last_peers]
        mean = sum(generativities) / len(generativities)
        variance = sum((g - mean) ** 2 for g in generativities) / len(generativities)
        return math.sqrt(variance)
