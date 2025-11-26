"""Unit tests for Regime Transition Ledger - Phase 11.3"""

import pytest
import tempfile
import time
from pathlib import Path
from datetime import datetime, timezone

from src.nova.continuity.regime_transition_ledger import (
    RegimeTransitionLedger,
    TransitionRecord,
    LedgerQueryResult,
    OscillationDetection,
    record_regime_transition,
    get_current_regime_duration,
)


@pytest.fixture
def temp_ledger():
    """Create temporary ledger for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        ledger_path = Path(tmpdir) / "test_ledger.jsonl"
        ledger = RegimeTransitionLedger(str(ledger_path))
        yield ledger


@pytest.fixture
def sample_factors():
    """Sample contributing factors."""
    return {
        "urf_composite_risk": 0.42,
        "mse_meta_instability": 0.08,
        "predictive_collapse_risk": 0.28,
        "consistency_gap": 0.12,
        "csi_continuity_index": 0.88
    }


# ---------- Record Transition Tests ----------


def test_record_transition_appends_to_ledger(temp_ledger, sample_factors):
    """Test transition record is appended to ledger."""
    result = temp_ledger.record_transition(
        from_regime="normal",
        to_regime="heightened",
        regime_score=0.35,
        contributing_factors=sample_factors,
        duration_in_previous_s=1200.5
    )

    assert result["success"] is True
    assert "record_id" in result

    # Verify written to file
    with open(temp_ledger.ledger_path, "r") as f:
        lines = f.readlines()
        assert len(lines) == 1


def test_record_transition_updates_current_regime(temp_ledger, sample_factors):
    """Test recording transition updates current regime state."""
    temp_ledger.record_transition(
        from_regime="normal",
        to_regime="heightened",
        regime_score=0.35,
        contributing_factors=sample_factors,
        duration_in_previous_s=1200.0
    )

    duration_info = temp_ledger.get_current_regime_duration()
    assert duration_info["regime"] == "heightened"
    assert duration_info["duration_s"] >= 0.0


def test_record_transition_computes_type_upgrade(temp_ledger, sample_factors):
    """Test transition type computed as 'upgrade' for more restrictive regime."""
    temp_ledger.record_transition(
        from_regime="normal",
        to_regime="emergency_stabilization",
        regime_score=0.75,
        contributing_factors=sample_factors,
        duration_in_previous_s=500.0
    )

    query_result = temp_ledger.query_transitions(limit=1)
    assert query_result.transitions[0].transition_type == "upgrade"


def test_record_transition_computes_type_downgrade(temp_ledger, sample_factors):
    """Test transition type computed as 'downgrade' for less restrictive regime."""
    # First transition to heightened
    temp_ledger.record_transition(
        from_regime="normal",
        to_regime="heightened",
        regime_score=0.35,
        contributing_factors=sample_factors,
        duration_in_previous_s=500.0
    )

    # Then downgrade back to normal
    temp_ledger.record_transition(
        from_regime="heightened",
        to_regime="normal",
        regime_score=0.20,
        contributing_factors=sample_factors,
        duration_in_previous_s=600.0
    )

    query_result = temp_ledger.query_transitions(limit=1)
    assert query_result.transitions[0].transition_type == "downgrade"


def test_record_transition_with_metadata(temp_ledger, sample_factors):
    """Test metadata is preserved in transition record."""
    metadata = {"trigger": "URF spike", "operator_note": "Expected during deployment"}

    temp_ledger.record_transition(
        from_regime="normal",
        to_regime="heightened",
        regime_score=0.35,
        contributing_factors=sample_factors,
        duration_in_previous_s=1200.0,
        metadata=metadata
    )

    query_result = temp_ledger.query_transitions(limit=1)
    assert query_result.transitions[0].metadata == metadata


# ---------- Current Regime Duration Tests ----------


def test_get_current_regime_duration_calculates_correctly(temp_ledger, sample_factors):
    """Test duration calculation for current regime."""
    temp_ledger.record_transition(
        from_regime="normal",
        to_regime="heightened",
        regime_score=0.35,
        contributing_factors=sample_factors,
        duration_in_previous_s=1200.0
    )

    time.sleep(0.1)  # Wait a bit

    duration_info = temp_ledger.get_current_regime_duration()
    assert duration_info["regime"] == "heightened"
    assert duration_info["duration_s"] >= 0.1
    assert "since_timestamp" in duration_info


def test_initial_state_zero_duration(temp_ledger):
    """Test initial state returns zero duration."""
    duration_info = temp_ledger.get_current_regime_duration()
    assert duration_info["regime"] == "normal"
    assert duration_info["duration_s"] == 0.0


# ---------- Query Transitions Tests ----------


def test_query_transitions_filters_by_time_window(temp_ledger, sample_factors):
    """Test query filters transitions by time window."""
    # Record 3 transitions
    temp_ledger.record_transition("normal", "heightened", 0.35, sample_factors, 100.0)
    time.sleep(0.05)
    start_time = datetime.now(timezone.utc).isoformat()
    time.sleep(0.05)
    temp_ledger.record_transition("heightened", "controlled_degradation", 0.55, sample_factors, 200.0)
    temp_ledger.record_transition("controlled_degradation", "heightened", 0.45, sample_factors, 150.0)

    # Query after start_time
    result = temp_ledger.query_transitions(start_time=start_time)
    assert result.total_count == 2


def test_query_transitions_filters_by_regime(temp_ledger, sample_factors):
    """Test query filters by from_regime and to_regime."""
    temp_ledger.record_transition("normal", "heightened", 0.35, sample_factors, 100.0)
    temp_ledger.record_transition("heightened", "normal", 0.20, sample_factors, 200.0)
    temp_ledger.record_transition("normal", "controlled_degradation", 0.55, sample_factors, 300.0)

    # Filter by from_regime
    result = temp_ledger.query_transitions(from_regime="normal")
    assert result.total_count == 2

    # Filter by to_regime
    result = temp_ledger.query_transitions(to_regime="heightened")
    assert result.total_count == 1


def test_query_transitions_respects_limit(temp_ledger, sample_factors):
    """Test query respects limit parameter."""
    # Record 5 transitions
    for i in range(5):
        temp_ledger.record_transition("normal", "heightened", 0.35, sample_factors, 100.0 * i)

    result = temp_ledger.query_transitions(limit=3)
    assert len(result.transitions) == 3
    assert result.total_count == 5


def test_query_transitions_newest_first(temp_ledger, sample_factors):
    """Test query returns transitions in descending timestamp order."""
    temp_ledger.record_transition("normal", "heightened", 0.35, sample_factors, 100.0)
    time.sleep(0.05)
    temp_ledger.record_transition("heightened", "controlled_degradation", 0.55, sample_factors, 200.0)

    result = temp_ledger.query_transitions()
    assert len(result.transitions) == 2
    # Newest first
    assert result.transitions[0].to_regime == "controlled_degradation"
    assert result.transitions[1].to_regime == "heightened"


# ---------- Oscillation Detection Tests ----------


def test_detect_oscillation_flags_rapid_transitions(temp_ledger, sample_factors):
    """Test oscillation detected with rapid transitions."""
    # Record 6 transitions (exceeds threshold of 5)
    for i in range(6):
        from_r = "normal" if i % 2 == 0 else "heightened"
        to_r = "heightened" if i % 2 == 0 else "normal"
        temp_ledger.record_transition(from_r, to_r, 0.35, sample_factors, 100.0)

    result = temp_ledger.detect_oscillation(window_s=3600, threshold=5)
    assert result.oscillation_detected is True
    assert result.transition_count == 6


def test_detect_oscillation_ignores_same_regime(temp_ledger, sample_factors):
    """Test oscillation detection ignores same→same transitions."""
    # Record same regime transitions (should not count)
    temp_ledger.record_transition("normal", "normal", 0.15, sample_factors, 100.0)
    temp_ledger.record_transition("normal", "normal", 0.15, sample_factors, 100.0)
    temp_ledger.record_transition("normal", "heightened", 0.35, sample_factors, 100.0)

    result = temp_ledger.detect_oscillation(window_s=3600, threshold=5)
    assert result.transition_count == 1  # Only the actual change


def test_detect_oscillation_respects_time_window(temp_ledger, sample_factors):
    """Test oscillation detection respects time window."""
    # Record 3 transitions, wait, then record 3 more
    for i in range(3):
        from_r = "normal" if i % 2 == 0 else "heightened"
        to_r = "heightened" if i % 2 == 0 else "normal"
        temp_ledger.record_transition(from_r, to_r, 0.35, sample_factors, 100.0)

    # Wait to age out old transitions
    time.sleep(0.15)

    for i in range(3):
        from_r = "normal" if i % 2 == 0 else "heightened"
        to_r = "heightened" if i % 2 == 0 else "normal"
        temp_ledger.record_transition(from_r, to_r, 0.35, sample_factors, 100.0)

    # Query with small window (should only see recent 3 transitions)
    result = temp_ledger.detect_oscillation(window_s=0.1, threshold=5)
    assert result.transition_count == 3
    assert result.oscillation_detected is False  # 3 < threshold of 5


# ---------- Continuity Invariant Tests ----------


def test_continuity_invariant(temp_ledger, sample_factors):
    """Test from_regime of record N+1 == to_regime of record N."""
    temp_ledger.record_transition("normal", "heightened", 0.35, sample_factors, 100.0)
    temp_ledger.record_transition("heightened", "controlled_degradation", 0.55, sample_factors, 200.0)
    temp_ledger.record_transition("controlled_degradation", "heightened", 0.45, sample_factors, 150.0)

    result = temp_ledger.query_transitions(limit=10)
    transitions = list(reversed(result.transitions))  # Chronological order

    for i in range(len(transitions) - 1):
        assert transitions[i].to_regime == transitions[i + 1].from_regime


# ---------- Persistence Tests ----------


def test_ledger_persists_across_instances(temp_ledger, sample_factors):
    """Test ledger data persists across instance reloads."""
    ledger_path = temp_ledger.ledger_path

    # Record transition
    temp_ledger.record_transition("normal", "heightened", 0.35, sample_factors, 1200.0)

    # Create new instance with same path
    new_ledger = RegimeTransitionLedger(str(ledger_path))

    # Verify loaded
    result = new_ledger.query_transitions()
    assert result.total_count == 1
    assert result.current_regime == "heightened"


# ---------- Flag Gating Tests ----------


def test_ledger_disabled_returns_empty(monkeypatch):
    """Test NOVA_ENABLE_REGIME_LEDGER=0 returns empty results."""
    monkeypatch.setenv("NOVA_ENABLE_REGIME_LEDGER", "0")

    result = record_regime_transition(
        from_regime="normal",
        to_regime="heightened",
        regime_score=0.35,
        contributing_factors={},
        duration_in_previous_s=1200.0
    )

    assert result["success"] is False
    assert result["reason"] == "ledger_disabled"


def test_ledger_disabled_duration_returns_defaults(monkeypatch):
    """Test disabled ledger returns default duration."""
    monkeypatch.setenv("NOVA_ENABLE_REGIME_LEDGER", "0")

    duration_info = get_current_regime_duration()
    assert duration_info["regime"] == "normal"
    assert duration_info["duration_s"] == 0.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
