"""Phase 6.0 Probabilistic Contracts - Belief Update Convergence Test."""

import pytest
import time
from unittest.mock import Mock, patch

from nova.belief_contracts import BeliefState, update_belief
from nova.slots.slot04_tri.core.tri_engine import TriEngine


class TestBeliefConvergence:
    """Test belief state convergence under various conditions."""

    def test_belief_update_convergence(self):
        """Test that belief updates converge when likelihood ≈ prior."""
        # Start with initial belief
        prior = BeliefState.from_point_estimate(0.5, 0.1)

        # Apply similar likelihood multiple times
        likelihood = BeliefState.from_point_estimate(0.52, 0.05)

        # Should converge toward likelihood with reduced variance
        for _ in range(10):
            prior = update_belief(prior, likelihood)

        # Check convergence properties
        assert abs(prior.mean - 0.52) < 0.1  # Converged toward likelihood
        assert prior.variance < 0.05  # Variance reduced
        assert prior.confidence > 0.8  # High confidence achieved

    def test_tri_engine_belief_publication(self):
        """Test TRI engine publishes belief states correctly."""
        engine = TriEngine()

        # Mock semantic mirror
        with patch('orchestrator.semantic_mirror.get_semantic_mirror') as mock_get_mirror:
            mock_mirror = Mock()
            mock_get_mirror.return_value = mock_mirror

            # Trigger assessment which should publish belief
            health = engine.assess()

            # Verify belief was published
            mock_mirror.publish_context.assert_called()
            call_args = mock_mirror.publish_context.call_args

            # Check belief state structure - should be BeliefState object
            belief = call_args[0][1]  # Second argument is the belief
            assert isinstance(belief, BeliefState)
            assert hasattr(belief, 'mean')
            assert hasattr(belief, 'variance')
            assert hasattr(belief, 'confidence')
            assert 0.0 <= belief.mean <= 1.0
            assert belief.variance >= 0.0

    def test_mirror_outage_graceful_degradation(self):
        """Test graceful degradation when semantic mirror is unavailable."""
        engine = TriEngine()

        # Mock mirror failure
        with patch('orchestrator.semantic_mirror.get_semantic_mirror') as mock_get_mirror:
            mock_get_mirror.side_effect = Exception("Mirror unavailable")

            # Should not raise exception
            health = engine.assess()

            # Should still return valid health data (Health is a dataclass)
            assert hasattr(health, 'tri_score')
            assert hasattr(health, 'coherence')
            assert health.tri_score is not None

    @pytest.mark.parametrize("initial_mean,likelihood_mean,expected_convergence", [
        (0.5, 0.5, 0.5),    # Identical values
        (0.3, 0.7, 0.55),   # Different values converge to weighted average
        (0.8, 0.2, 0.35),   # Large difference converges to middle
    ])
    def test_belief_convergence_matrix(self, initial_mean, likelihood_mean, expected_convergence):
        """Test convergence across different initial conditions."""
        prior = BeliefState.from_point_estimate(initial_mean, 0.1)
        likelihood = BeliefState.from_point_estimate(likelihood_mean, 0.1)

        # Multiple updates to reach convergence
        for _ in range(20):
            prior = update_belief(prior, likelihood)

        # Should converge toward expected value (precision-weighted average)
        assert abs(prior.mean - expected_convergence) < 0.15  # Allow more tolerance for convergence
        assert prior.variance < 0.01  # Very low variance after convergence

    def test_belief_temporal_decay(self):
        """Test belief variance increases with staleness."""
        fresh_belief = BeliefState(mean=0.5, variance=0.01, timestamp=time.time())

        # Simulate time passage
        stale_belief = fresh_belief.decayed(time_since_update=300, decay_rate=0.1)

        # Variance should increase
        assert stale_belief.variance > fresh_belief.variance
        # Mean should remain constant
        assert stale_belief.mean == fresh_belief.mean
        # Confidence should decrease
        assert stale_belief.confidence < fresh_belief.confidence