"""
Tests for MockPeerService (Phase 16-1).

Validates synthetic peer generation for offline federation testing.
"""

import os
import pytest

from nova.federation.mock_peer_service import MockPeerService


class TestMockPeerService:
    """Test suite for MockPeerService."""

    def test_deterministic_seed_reproducibility(self):
        """
        Test that same seed produces identical peer populations.

        Validates:
            - Deterministic generation with seed
            - Reproducibility across instances
            - All attributes match (peer_id, quality, stability, generativity)
        """
        seed = 42

        # Generate first population
        service1 = MockPeerService(seed=seed)
        peers1 = service1.generate_peers(5)

        # Generate second population with same seed
        service2 = MockPeerService(seed=seed)
        peers2 = service2.generate_peers(5)

        # Verify identical results
        assert len(peers1) == len(peers2) == 5
        for p1, p2 in zip(peers1, peers2):
            assert p1.peer_id == p2.peer_id
            assert p1.peer_quality == p2.peer_quality
            assert p1.stability_margin == p2.stability_margin
            assert p1.generativity == p2.generativity

    def test_variance_calculation(self):
        """
        Test get_peer_variance() computes standard deviation correctly.

        Validates:
            - Variance returns 0.0 for < 2 peers
            - Variance > 0 for peers with different generativity
            - Variance calculation matches std_dev formula
        """
        # Single peer: variance should be 0
        service = MockPeerService(seed=100)
        peers = service.generate_peers(1)
        variance = service.get_peer_variance()
        assert variance == 0.0, "Single peer should have 0 variance"

        # Multiple peers: variance should be > 0
        service = MockPeerService(seed=200)
        peers = service.generate_peers(5)
        variance = service.get_peer_variance()
        assert variance > 0.0, "Multiple peers should have non-zero variance"

        # Manually verify calculation
        generativities = [p.generativity for p in peers]
        mean = sum(generativities) / len(generativities)
        expected_var = sum((g - mean) ** 2 for g in generativities) / len(generativities)
        expected_std = expected_var ** 0.5
        assert abs(variance - expected_std) < 1e-9, "Variance calculation mismatch"

    def test_peer_count_matches_request(self):
        """
        Test that generated peer count matches requested count.

        Validates:
            - Count range [1, 10] respected
            - ValueError raised for out-of-range counts
        """
        service = MockPeerService(seed=300)

        # Valid counts: 1-10
        for count in [1, 3, 5, 7, 10]:
            peers = service.generate_peers(count)
            assert len(peers) == count, f"Expected {count} peers, got {len(peers)}"

        # Invalid counts: 0, 11
        with pytest.raises(ValueError, match="peer count must be in"):
            service.generate_peers(0)

        with pytest.raises(ValueError, match="peer count must be in"):
            service.generate_peers(11)

    def test_quality_stability_bounds_respected(self):
        """
        Test that generated peer attributes respect bounds.

        Validates:
            - peer_quality ∈ [0.4, 0.9]
            - stability_margin ∈ [0.02, 0.05]
            - generativity ∈ [0.2, 0.7]
            - All attributes are valid floats
        """
        service = MockPeerService(seed=400)
        peers = service.generate_peers(10)

        for peer in peers:
            # Peer ID: should be valid UUIDv7 string
            assert isinstance(peer.peer_id, str)
            assert len(peer.peer_id) == 36  # UUID format: 8-4-4-4-12

            # Quality bounds
            assert 0.4 <= peer.peer_quality <= 0.9, (
                f"peer_quality {peer.peer_quality} out of bounds [0.4, 0.9]"
            )

            # Stability bounds
            assert 0.02 <= peer.stability_margin <= 0.05, (
                f"stability_margin {peer.stability_margin} out of bounds [0.02, 0.05]"
            )

            # Generativity bounds
            assert 0.2 <= peer.generativity <= 0.7, (
                f"generativity {peer.generativity} out of bounds [0.2, 0.7]"
            )

    def test_environment_variable_std_override(self):
        """
        Test that NOVA_FED_MOCK_STD environment variable controls variance.

        Validates:
            - Default std = 0.15
            - Environment override works
            - Clamping to [0.05, 0.30] range
        """
        # Save original env var
        original_std = os.environ.get("NOVA_FED_MOCK_STD")

        try:
            # Test default (no env var)
            if "NOVA_FED_MOCK_STD" in os.environ:
                del os.environ["NOVA_FED_MOCK_STD"]
            service = MockPeerService(seed=500)
            assert service._std == 0.15, "Default std should be 0.15"

            # Test valid override
            os.environ["NOVA_FED_MOCK_STD"] = "0.20"
            service = MockPeerService(seed=500)
            assert service._std == 0.20, "Std should respect env override"

            # Test clamping: too low
            os.environ["NOVA_FED_MOCK_STD"] = "0.01"
            service = MockPeerService(seed=500)
            assert service._std == 0.05, "Std should clamp to minimum 0.05"

            # Test clamping: too high
            os.environ["NOVA_FED_MOCK_STD"] = "0.50"
            service = MockPeerService(seed=500)
            assert service._std == 0.30, "Std should clamp to maximum 0.30"

            # Test invalid value (non-numeric)
            os.environ["NOVA_FED_MOCK_STD"] = "invalid"
            service = MockPeerService(seed=500)
            assert service._std == 0.15, "Invalid value should default to 0.15"

        finally:
            # Restore original env var
            if original_std is not None:
                os.environ["NOVA_FED_MOCK_STD"] = original_std
            elif "NOVA_FED_MOCK_STD" in os.environ:
                del os.environ["NOVA_FED_MOCK_STD"]

    def test_novelty_increases_with_variance(self):
        """
        Test that novelty (variance) increases with higher NOVA_FED_MOCK_STD.

        Validates:
            - Higher std → higher peer diversity
            - Variance measurement reflects configured std
        """
        original_std = os.environ.get("NOVA_FED_MOCK_STD")

        try:
            # Low variance
            os.environ["NOVA_FED_MOCK_STD"] = "0.05"
            service_low = MockPeerService(seed=600)
            peers_low = service_low.generate_peers(10)
            variance_low = service_low.get_peer_variance()

            # High variance
            os.environ["NOVA_FED_MOCK_STD"] = "0.25"
            service_high = MockPeerService(seed=600)
            peers_high = service_high.generate_peers(10)
            variance_high = service_high.get_peer_variance()

            # Higher std should produce higher variance
            assert variance_high > variance_low, (
                f"High std variance ({variance_high}) should exceed "
                f"low std variance ({variance_low})"
            )

        finally:
            # Restore original env var
            if original_std is not None:
                os.environ["NOVA_FED_MOCK_STD"] = original_std
            elif "NOVA_FED_MOCK_STD" in os.environ:
                del os.environ["NOVA_FED_MOCK_STD"]
