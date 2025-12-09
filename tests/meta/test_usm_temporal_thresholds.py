"""
Tests for provisional temporal USM threshold classification (Phase 14.5).

These tests validate the classification logic using pilot observation results:
- Benign: ρ_t rises to 0.6 during reciprocity
- Extractive: ρ_t flat at 0.0 throughout
- VOID: ρ_t=1.0, C_t=0.0

Thresholds are PROVISIONAL and expected to require refinement after
100-200 real observation sessions.
"""

import pytest

from nova.math.usm_temporal_thresholds import (
    DEFAULT_THRESHOLDS,
    TemporalThresholds,
    classify_temporal_state,
)


class TestTemporalThresholds:
    """Test provisional threshold dataclass."""

    def test_default_thresholds_values(self):
        """Verify default thresholds match Phase 14.5 pilot calibration."""
        assert DEFAULT_THRESHOLDS.extractive_C == 0.18
        assert DEFAULT_THRESHOLDS.protective_C == -0.12
        assert DEFAULT_THRESHOLDS.extractive_rho == 0.25
        assert DEFAULT_THRESHOLDS.protective_rho == 0.6
        assert DEFAULT_THRESHOLDS.min_turns == 3

    def test_custom_thresholds(self):
        """Verify custom thresholds can be instantiated."""
        custom = TemporalThresholds(
            extractive_C=0.2,
            protective_C=-0.15,
            extractive_rho=0.3,
            protective_rho=0.7,
            min_turns=5,
        )
        assert custom.extractive_C == 0.2
        assert custom.min_turns == 5

    def test_thresholds_immutable(self):
        """Verify thresholds are frozen (immutable)."""
        with pytest.raises(AttributeError):
            DEFAULT_THRESHOLDS.extractive_C = 0.5  # type: ignore


class TestClassifyTemporalState:
    """Test state classification logic."""

    def test_warming_up_insufficient_turns(self):
        """Early conversation returns warming_up before min_turns."""
        assert classify_temporal_state(C_t=0.0, rho_t=0.5, turn_count=0) == "warming_up"
        assert classify_temporal_state(C_t=0.0, rho_t=0.5, turn_count=2) == "warming_up"

    def test_extractive_high_collapse_low_reciprocity(self):
        """High C_t + low ρ_t = extractive (hierarchical control)."""
        # Pilot observation: extractive scenario had C_t spike to 0.2, ρ_t=0.0
        assert classify_temporal_state(C_t=0.2, rho_t=0.0, turn_count=5) == "extractive"
        assert classify_temporal_state(C_t=0.18, rho_t=0.24, turn_count=10) == "extractive"

    def test_consensus_low_collapse_low_reciprocity(self):
        """Low C_t + low ρ_t = consensus (aligned cooperation, not extraction)."""
        # Pilot observation: benign conversation ended with C_t=-0.1, ρ_t=0.015
        assert classify_temporal_state(C_t=-0.15, rho_t=0.1, turn_count=10) == "consensus"
        assert classify_temporal_state(C_t=-0.2, rho_t=0.0, turn_count=5) == "consensus"

    def test_collaborative_low_collapse_high_reciprocity(self):
        """Low C_t + high ρ_t = collaborative (active negotiation)."""
        # Must be below protective_C threshold (-0.12) AND above protective_rho (0.6)
        assert classify_temporal_state(C_t=-0.13, rho_t=0.6, turn_count=6) == "collaborative"
        assert classify_temporal_state(C_t=-0.15, rho_t=0.8, turn_count=10) == "collaborative"

    def test_neutral_middle_range(self):
        """Mid-range C_t and ρ_t = neutral."""
        assert classify_temporal_state(C_t=0.0, rho_t=0.4, turn_count=5) == "neutral"
        assert classify_temporal_state(C_t=-0.05, rho_t=0.5, turn_count=10) == "neutral"

    def test_pilot_benign_trajectory(self):
        """Validate classification against pilot benign scenario trajectory."""
        # Turn 1-5: warming up, low reciprocity
        assert classify_temporal_state(C_t=-0.1, rho_t=0.0, turn_count=2) == "warming_up"

        # Turn 6: reciprocity emerges (Bob supports Carol) - but C_t=0.02 in neutral range
        # Actual pilot: C_t=0.02 is above protective threshold, so classified as neutral
        assert classify_temporal_state(C_t=0.02, rho_t=0.6, turn_count=6) == "neutral"

        # Turn 10: consensus (all agree, reciprocity decayed) - C_t=-0.097 also in neutral
        assert classify_temporal_state(C_t=-0.097, rho_t=0.015, turn_count=10) == "neutral"

    def test_pilot_extractive_trajectory(self):
        """Validate classification against pilot extractive scenario."""
        # Throughout: flat ρ_t=0.0, C_t oscillates
        # C_t=-0.1 in neutral range (above protective threshold -0.12)
        assert classify_temporal_state(C_t=-0.1, rho_t=0.0, turn_count=5) == "neutral"
        # C_t=0.2 above extractive threshold (0.18)
        assert classify_temporal_state(C_t=0.2, rho_t=0.0, turn_count=7) == "extractive"

    def test_pilot_void_state(self):
        """VOID state: C_t=0, ρ_t=1.0 -> neutral (equilibrium, no action needed)."""
        assert classify_temporal_state(C_t=0.0, rho_t=1.0, turn_count=5) == "neutral"

    def test_custom_thresholds_applied(self):
        """Verify custom thresholds override defaults."""
        custom = TemporalThresholds(
            extractive_C=0.1,
            protective_C=-0.2,
            extractive_rho=0.3,
            protective_rho=0.7,
            min_turns=5,
        )

        # Turn 4: still warming up with custom min_turns=5
        assert (
            classify_temporal_state(C_t=0.0, rho_t=0.5, turn_count=4, thresholds=custom)
            == "warming_up"
        )

        # Turn 6: meets custom thresholds
        assert (
            classify_temporal_state(C_t=0.11, rho_t=0.2, turn_count=6, thresholds=custom)
            == "extractive"
        )

    def test_boundary_conditions(self):
        """Test exact threshold boundaries."""
        # Exactly at extractive C threshold
        assert classify_temporal_state(C_t=0.18, rho_t=0.2, turn_count=5) == "extractive"

        # Just below extractive C threshold
        assert classify_temporal_state(C_t=0.17, rho_t=0.2, turn_count=5) == "neutral"

        # Exactly at protective C threshold
        assert classify_temporal_state(C_t=-0.12, rho_t=0.2, turn_count=5) == "consensus"

        # Just above protective C threshold
        assert classify_temporal_state(C_t=-0.11, rho_t=0.2, turn_count=5) == "neutral"
