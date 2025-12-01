# tests/continuity/test_temporal_snapshot.py

import pytest
import time
from unittest.mock import patch

from src.nova.continuity.temporal_snapshot import (
    RegimeSnapshot,
    make_snapshot,
)


class TestRegimeSnapshot:
    """Test the RegimeSnapshot dataclass."""

    def test_snapshot_creation(self):
        """Test basic snapshot creation."""
        snapshot = RegimeSnapshot(
            regime="normal",
            previous_regime="heightened",
            timestamp_s=1640995200.0,
            time_in_regime_s=3600.0,
            time_in_previous_regime_s=7200.0,
            regime_score=0.15,
            regime_factors={"urf": 0.1, "mse": 0.05},
        )

        assert snapshot.regime == "normal"
        assert snapshot.previous_regime == "heightened"
        assert snapshot.timestamp_s == 1640995200.0
        assert snapshot.time_in_regime_s == 3600.0
        assert snapshot.time_in_previous_regime_s == 7200.0
        assert snapshot.regime_score == 0.15
        assert snapshot.regime_factors == {"urf": 0.1, "mse": 0.05}

    def test_snapshot_immutability(self):
        """Test that snapshots are immutable."""
        snapshot = RegimeSnapshot(
            regime="normal",
            previous_regime="heightened",
            timestamp_s=1640995200.0,
            time_in_regime_s=3600.0,
            time_in_previous_regime_s=7200.0,
            regime_score=0.15,
            regime_factors={"urf": 0.1, "mse": 0.05},
        )

        with pytest.raises(AttributeError):
            snapshot.regime = "heightened"

    def test_to_dict_conversion(self):
        """Test deterministic dict conversion."""
        snapshot = RegimeSnapshot(
            regime="normal",
            previous_regime="heightened",
            timestamp_s=1640995200.0,
            time_in_regime_s=3600.0,
            time_in_previous_regime_s=7200.0,
            regime_score=0.15,
            regime_factors={"urf": 0.1, "mse": 0.05},
            dual_modality_state="agreed",
            drift_detected=False,
            oracle_classification="normal",
            hash_prev="abc123",
        )

        result = snapshot.to_dict()

        expected = {
            "regime": "normal",
            "previous_regime": "heightened",
            "timestamp_s": 1640995200.0,
            "time_in_regime_s": 3600.0,
            "time_in_previous_regime_s": 7200.0,
            "regime_score": 0.15,
            "regime_factors": {"urf": 0.1, "mse": 0.05},
            "dual_modality_state": "agreed",
            "drift_detected": False,
            "oracle_classification": "normal",
            "hash_prev": "abc123",
        }

        assert result == expected

    def test_to_dict_deterministic(self):
        """Test that to_dict() produces deterministic output."""
        snapshot = RegimeSnapshot(
            regime="normal",
            previous_regime="heightened",
            timestamp_s=1640995200.0,
            time_in_regime_s=3600.0,
            time_in_previous_regime_s=7200.0,
            regime_score=0.15,
            regime_factors={"mse": 0.05, "urf": 0.1},  # Different order
        )

        result1 = snapshot.to_dict()
        result2 = snapshot.to_dict()

        assert result1 == result2
        # Note: dict ordering may vary, but values should be consistent


class TestMakeSnapshot:
    """Test the make_snapshot factory function."""

    @patch('src.nova.continuity.temporal_snapshot.time.time')
    def test_make_snapshot_basic(self, mock_time):
        """Test basic snapshot creation with make_snapshot."""
        mock_time.return_value = 1640995200.0

        snapshot = make_snapshot(
            regime="normal",
            previous_regime="heightened",
            time_in_regime_s=3600.0,
            time_in_previous_regime_s=7200.0,
            regime_score=0.15,
            regime_factors={"urf": 0.1, "mse": 0.05},
        )

        assert snapshot.regime == "normal"
        assert snapshot.previous_regime == "heightened"
        assert snapshot.timestamp_s == 1640995200.0
        assert snapshot.time_in_regime_s == 3600.0
        assert snapshot.time_in_previous_regime_s == 7200.0
        assert snapshot.regime_score == 0.15
        assert snapshot.regime_factors == {"urf": 0.1, "mse": 0.05}

    @patch('src.nova.continuity.temporal_snapshot.time.time')
    def test_make_snapshot_with_optional_fields(self, mock_time):
        """Test snapshot creation with optional fields."""
        mock_time.return_value = 1640995200.0

        snapshot = make_snapshot(
            regime="heightened",
            previous_regime="normal",
            time_in_regime_s=1800.0,
            time_in_previous_regime_s=3600.0,
            regime_score=0.75,
            regime_factors={"urf": 0.8, "mse": 0.7},
            dual_modality_state="disagreed",
            drift_detected=True,
            oracle_classification="emergency_stabilization",
            hash_prev="def456",
        )

        assert snapshot.regime == "heightened"
        assert snapshot.dual_modality_state == "disagreed"
        assert snapshot.drift_detected is True
        assert snapshot.oracle_classification == "emergency_stabilization"
        assert snapshot.hash_prev == "def456"

    @patch('src.nova.continuity.temporal_snapshot.time.time')
    def test_make_snapshot_custom_timestamp(self, mock_time):
        """Test snapshot creation with custom timestamp."""
        custom_time = 1640995300.0

        snapshot = make_snapshot(
            regime="normal",
            previous_regime="heightened",
            time_in_regime_s=3600.0,
            time_in_previous_regime_s=7200.0,
            regime_score=0.15,
            regime_factors={"urf": 0.1, "mse": 0.05},
            timestamp_s=custom_time,
        )

        assert snapshot.timestamp_s == custom_time
        # time.time should not be called when timestamp_s is provided
        mock_time.assert_not_called()

    def test_make_snapshot_default_optional_fields(self):
        """Test that optional fields have correct defaults."""
        snapshot = make_snapshot(
            regime="normal",
            previous_regime="heightened",
            time_in_regime_s=3600.0,
            time_in_previous_regime_s=7200.0,
            regime_score=0.15,
            regime_factors={"urf": 0.1, "mse": 0.05},
        )

        assert snapshot.dual_modality_state is None
        assert snapshot.drift_detected is False
        assert snapshot.oracle_classification is None
        assert snapshot.hash_prev is None


class TestPhase13bCompliance:
    """Test Phase 13b compliance requirements."""

    def test_pre_transition_snapshot_structure(self):
        """Test that snapshot contains all required pre-transition fields."""
        snapshot = make_snapshot(
            regime="normal",
            previous_regime="heightened",
            time_in_regime_s=3600.0,
            time_in_previous_regime_s=7200.0,
            regime_score=0.15,
            regime_factors={"urf": 0.1, "mse": 0.05},
        )

        # Required fields from Mother Ontology v1.7.1
        assert hasattr(snapshot, 'regime')
        assert hasattr(snapshot, 'previous_regime')
        assert hasattr(snapshot, 'timestamp_s')
        assert hasattr(snapshot, 'time_in_regime_s')
        assert hasattr(snapshot, 'time_in_previous_regime_s')
        assert hasattr(snapshot, 'regime_score')
        assert hasattr(snapshot, 'regime_factors')

        # Phase 13b specific fields
        assert hasattr(snapshot, 'dual_modality_state')
        assert hasattr(snapshot, 'drift_detected')
        assert hasattr(snapshot, 'oracle_classification')

    def test_snapshot_immutable_for_ledger(self):
        """Test that snapshot immutability supports ledger hashing."""
        snapshot = make_snapshot(
            regime="normal",
            previous_regime="heightened",
            time_in_regime_s=3600.0,
            time_in_previous_regime_s=7200.0,
            regime_score=0.15,
            regime_factors={"urf": 0.1, "mse": 0.05},
        )

        # Should be immutable for deterministic hashing
        dict1 = snapshot.to_dict()
        dict2 = snapshot.to_dict()
        assert dict1 == dict2

        # Should not be modifiable after creation
        with pytest.raises(AttributeError):
            snapshot.regime = "heightened"

    def test_oracle_evaluation_context(self):
        """Test that snapshot provides context for oracle evaluation."""
        snapshot = make_snapshot(
            regime="heightened",
            previous_regime="normal",
            time_in_regime_s=1800.0,  # Pre-transition duration
            time_in_previous_regime_s=3600.0,
            regime_score=0.75,
            regime_factors={"urf": 0.8, "mse": 0.7},
        )

        # Oracle should evaluate using pre-transition state
        # This enables detection of illegal transitions
        assert snapshot.regime == "heightened"  # Current (pre-transition)
        assert snapshot.previous_regime == "normal"  # Previous regime
        assert snapshot.time_in_regime_s == 1800.0  # Time in current regime
        assert snapshot.time_in_previous_regime_s == 3600.0  # Time in previous regime
