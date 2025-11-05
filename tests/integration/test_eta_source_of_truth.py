"""
Integration test: GovernorState as single source of truth for η.

Verifies that:
1. Training loops read η from GovernorState
2. Frozen state correctly returns 0.0
3. State changes are immediately visible
"""

import pytest

from nova.governor import state as governor_state


def setup_function():
    """Reset state before each test."""
    governor_state.reset_for_tests(eta=0.10, frozen=False)


def test_eta_source_of_truth():
    """Test that get_training_eta() reads from GovernorState."""
    # Set eta to specific value
    governor_state.set_eta(0.15)

    # Training hook should return that value
    eta = governor_state.get_training_eta()
    assert eta == pytest.approx(0.15)


def test_frozen_returns_zero_eta():
    """Test that frozen state returns 0.0 to halt learning."""
    # Set eta to non-zero value
    governor_state.set_eta(0.12)

    # Freeze learning
    governor_state.set_frozen(True)

    # Training hook should return 0.0 (frozen)
    eta = governor_state.get_training_eta()
    assert eta == pytest.approx(0.0)


def test_unfreezing_resumes_normal_eta():
    """Test that unfreezing resumes normal eta value."""
    governor_state.set_eta(0.14)
    governor_state.set_frozen(True)

    # Verify frozen
    assert governor_state.get_training_eta() == pytest.approx(0.0)

    # Unfreeze
    governor_state.set_frozen(False)

    # Should resume normal eta
    assert governor_state.get_training_eta() == pytest.approx(0.14)


def test_eta_updates_immediately_visible():
    """Test that eta updates are immediately visible to all readers."""
    governor_state.set_eta(0.10)
    assert governor_state.get_training_eta() == pytest.approx(0.10)

    governor_state.set_eta(0.15)
    assert governor_state.get_training_eta() == pytest.approx(0.15)

    governor_state.set_eta(0.08)
    assert governor_state.get_training_eta() == pytest.approx(0.08)


def test_multiple_readers_see_same_value():
    """Test that multiple readers see consistent value."""
    governor_state.set_eta(0.13)

    # Simulate multiple training loops reading
    eta_values = [governor_state.get_training_eta() for _ in range(10)]

    # All should see the same value
    assert all(eta == pytest.approx(0.13) for eta in eta_values)


def test_state_isolation():
    """Test that get_eta() and get_training_eta() behave correctly."""
    governor_state.set_eta(0.12)
    governor_state.set_frozen(True)

    # get_eta() returns raw value
    assert governor_state.get_eta() == pytest.approx(0.12)

    # get_training_eta() returns 0.0 when frozen
    assert governor_state.get_training_eta() == pytest.approx(0.0)

    # get_state() returns both
    eta, frozen = governor_state.get_state()
    assert eta == pytest.approx(0.12)
    assert frozen is True
