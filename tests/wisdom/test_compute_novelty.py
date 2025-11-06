"""
Tests for compute_novelty function (Phase 16-1).

Validates Novelty (N) computation from peer diversity.
"""

import pytest

from nova.wisdom.generativity_core import compute_novelty
from nova.federation.schemas import PeerSummary


def test_compute_novelty_zero_peers():
    """Test that compute_novelty returns 0.0 for empty peer list."""
    peers = []
    N = compute_novelty(peers)
    assert N == 0.0


def test_compute_novelty_single_peer():
    """Test that compute_novelty returns 0.0 for single peer (no diversity)."""
    peers = [
        PeerSummary(
            peer_id="peer-1",
            peer_quality=0.7,
            stability_margin=0.03,
            generativity=0.5
        )
    ]
    N = compute_novelty(peers)
    assert N == 0.0


def test_compute_novelty_multiple_peers_identical():
    """Test novelty for identical peers (zero variance)."""
    peers = [
        PeerSummary(
            peer_id=f"peer-{i}",
            peer_quality=0.7,
            stability_margin=0.03,
            generativity=0.5  # All identical
        )
        for i in range(5)
    ]
    N = compute_novelty(peers)
    assert N == 0.0


def test_compute_novelty_multiple_peers_diverse():
    """Test novelty for diverse peers (non-zero variance)."""
    peers = [
        PeerSummary(
            peer_id="peer-1",
            peer_quality=0.7,
            stability_margin=0.03,
            generativity=0.3
        ),
        PeerSummary(
            peer_id="peer-2",
            peer_quality=0.8,
            stability_margin=0.04,
            generativity=0.5
        ),
        PeerSummary(
            peer_id="peer-3",
            peer_quality=0.6,
            stability_margin=0.02,
            generativity=0.7
        ),
    ]
    N = compute_novelty(peers)

    # Should be non-zero with variance
    assert N > 0.0

    # Manually calculate expected value
    generativities = [0.3, 0.5, 0.7]
    mean = sum(generativities) / len(generativities)  # 0.5
    variance = sum((g - mean) ** 2 for g in generativities) / len(generativities)
    std_dev = variance ** 0.5  # ~0.1633
    expected_N = min(1.0, std_dev / 0.5)  # ~0.3266

    assert abs(N - expected_N) < 1e-6


def test_compute_novelty_clipping():
    """Test that novelty is clipped to [0, 1] range."""
    # Create peers with very high variance (artificially)
    # Max generativity range is [0.2, 0.7], so std_dev can't exceed ~0.2
    peers = [
        PeerSummary(
            peer_id="peer-1",
            peer_quality=0.7,
            stability_margin=0.03,
            generativity=0.2  # Min
        ),
        PeerSummary(
            peer_id="peer-2",
            peer_quality=0.8,
            stability_margin=0.04,
            generativity=0.7  # Max
        ),
    ]
    N = compute_novelty(peers)

    # Should be clipped to [0, 1]
    assert 0.0 <= N <= 1.0

    # With generativity range [0.2, 0.7], std_dev = 0.25
    # N = 0.25 / 0.5 = 0.5
    assert abs(N - 0.5) < 1e-6


def test_compute_novelty_integration_with_mock_service():
    """
    Integration test: compute_novelty works with MockPeerService output.
    """
    from nova.federation.mock_peer_service import MockPeerService

    # Generate mock peers
    service = MockPeerService(seed=12345)
    peers = service.generate_peers(5)

    # Compute novelty
    N = compute_novelty(peers)

    # Should be non-zero for multiple peers
    assert N > 0.0
    assert N <= 1.0

    # Should match service's own variance calculation (within normalization)
    variance_raw = service.get_peer_variance()
    N_from_variance = min(1.0, variance_raw / 0.5)
    assert abs(N - N_from_variance) < 1e-6
