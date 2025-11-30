"""Unit tests for ORP Hysteresis Enforcement - Phase 11.4"""

import pytest
from datetime import datetime, timedelta, timezone
from src.nova.continuity.orp_hysteresis import (
    check_regime_hysteresis,
    get_hysteresis_metrics,
    stabilize_recovery_ramp,
    MIN_REGIME_DURATIONS,
    OSCILLATION_WINDOW_S,
    OSCILLATION_THRESHOLD,
    HysteresisDecision,
)


# ---------- Constants Verification Tests ----------


def test_min_regime_durations_structure():
    """Test minimum regime durations are defined for all regimes."""
    assert "normal" in MIN_REGIME_DURATIONS
    assert "heightened" in MIN_REGIME_DURATIONS
    assert "controlled_degradation" in MIN_REGIME_DURATIONS
    assert "emergency_stabilization" in MIN_REGIME_DURATIONS
    assert "recovery" in MIN_REGIME_DURATIONS

    # Verify durations are positive
    for regime, duration in MIN_REGIME_DURATIONS.items():
        assert duration > 0.0, f"Regime {regime} has non-positive duration"


def test_min_regime_durations_values():
    """Test minimum regime durations match contract spec."""
    assert MIN_REGIME_DURATIONS["normal"] == 60.0
    assert MIN_REGIME_DURATIONS["heightened"] == 300.0
    assert MIN_REGIME_DURATIONS["controlled_degradation"] == 600.0
    assert MIN_REGIME_DURATIONS["emergency_stabilization"] == 900.0
    assert MIN_REGIME_DURATIONS["recovery"] == 1800.0


def test_oscillation_constants():
    """Test oscillation detection constants."""
    assert OSCILLATION_WINDOW_S == 300.0  # 5 minutes
    assert OSCILLATION_THRESHOLD == 3     # 3 transitions


# ---------- check_regime_hysteresis Tests ----------


def test_check_regime_hysteresis_empty_ledger():
    """Test hysteresis check with empty ledger (bootstrap case)."""
    decision = check_regime_hysteresis("normal", [])

    assert decision.allowed is True
    assert decision.effective_regime == "normal"
    assert decision.reason == "no_ledger_history"
    assert decision.current_regime == "unknown"


def test_check_regime_hysteresis_same_regime():
    """Test hysteresis check when proposed == current (no transition)."""
    ledger = [
        {"regime": "normal", "timestamp": "2025-01-01T00:00:00Z", "duration_s": 100.0}
    ]
    decision = check_regime_hysteresis("normal", ledger)

    assert decision.allowed is True
    assert decision.effective_regime == "normal"
    assert decision.reason == "same_regime_no_transition"
    assert decision.time_remaining_s == 0.0


def test_check_regime_hysteresis_min_duration_not_met():
    """Test hysteresis blocks transition when minimum duration not met."""
    # Heightened requires 300s, only been 100s
    ledger = [
        {"regime": "heightened", "timestamp": "2025-01-01T00:00:00Z", "duration_s": 100.0}
    ]
    decision = check_regime_hysteresis("normal", ledger)

    assert decision.allowed is False
    assert decision.effective_regime == "heightened"  # Stay in current regime
    assert "min_duration_not_met" in decision.reason
    assert decision.current_duration_s == 100.0
    assert decision.min_duration_s == 300.0
    assert decision.time_remaining_s == 200.0  # 300 - 100


def test_check_regime_hysteresis_min_duration_met():
    """Test hysteresis allows transition when minimum duration met."""
    # Heightened requires 300s, been 400s
    ledger = [
        {"regime": "heightened", "timestamp": "2025-01-01T00:00:00Z", "duration_s": 400.0}
    ]
    decision = check_regime_hysteresis("normal", ledger)

    assert decision.allowed is True
    assert decision.effective_regime == "normal"
    assert "min_duration_met" in decision.reason
    assert decision.time_remaining_s == 0.0


def test_check_regime_hysteresis_normal_short_duration():
    """Test normal regime (60s minimum) allows transition quickly."""
    # Normal requires 60s, been 70s
    ledger = [
        {"regime": "normal", "timestamp": "2025-01-01T00:00:00Z", "duration_s": 70.0}
    ]
    decision = check_regime_hysteresis("heightened", ledger)

    assert decision.allowed is True
    assert decision.effective_regime == "heightened"


def test_check_regime_hysteresis_emergency_long_duration():
    """Test emergency regime (900s minimum) blocks premature transition."""
    # Emergency requires 900s, only been 500s
    ledger = [
        {"regime": "emergency_stabilization", "timestamp": "2025-01-01T00:00:00Z", "duration_s": 500.0}
    ]
    decision = check_regime_hysteresis("recovery", ledger)

    assert decision.allowed is False
    assert decision.effective_regime == "emergency_stabilization"
    assert decision.time_remaining_s == 400.0  # 900 - 500


def test_check_regime_hysteresis_recovery_very_long():
    """Test recovery regime (1800s minimum) requires patience."""
    # Recovery requires 1800s, only been 1000s
    ledger = [
        {"regime": "recovery", "timestamp": "2025-01-01T00:00:00Z", "duration_s": 1000.0}
    ]
    decision = check_regime_hysteresis("normal", ledger)

    assert decision.allowed is False
    assert decision.effective_regime == "recovery"
    assert decision.time_remaining_s == 800.0  # 1800 - 1000


def test_check_regime_hysteresis_case_insensitive():
    """Test regime names are case-insensitive."""
    ledger = [
        {"regime": "HEIGHTENED", "timestamp": "2025-01-01T00:00:00Z", "duration_s": 400.0}
    ]
    decision = check_regime_hysteresis("Normal", ledger)

    assert decision.allowed is True
    assert decision.effective_regime == "Normal"


def test_check_regime_hysteresis_whitespace_trimmed():
    """Test regime names are trimmed of whitespace."""
    ledger = [
        {"regime": " heightened ", "timestamp": "2025-01-01T00:00:00Z", "duration_s": 400.0}
    ]
    decision = check_regime_hysteresis("  normal  ", ledger)

    assert decision.allowed is True


# ---------- Oscillation Detection Tests ----------


def test_check_regime_hysteresis_oscillation_detected():
    """Test oscillation detection when rapid switches occur."""
    now = datetime.now(timezone.utc)

    # Create ledger with 4 transitions in 5 minutes (oscillating)
    ledger = [
        {"regime": "normal", "timestamp": (now - timedelta(seconds=290)).isoformat().replace('+00:00', 'Z'), "duration_s": 10.0},
        {"regime": "heightened", "timestamp": (now - timedelta(seconds=280)).isoformat().replace('+00:00', 'Z'), "duration_s": 10.0},
        {"regime": "normal", "timestamp": (now - timedelta(seconds=270)).isoformat().replace('+00:00', 'Z'), "duration_s": 10.0},
        {"regime": "heightened", "timestamp": (now - timedelta(seconds=260)).isoformat().replace('+00:00', 'Z'), "duration_s": 10.0},
        {"regime": "normal", "timestamp": now.isoformat().replace('+00:00', 'Z'), "duration_s": 260.0},  # Current
    ]

    decision = check_regime_hysteresis("heightened", ledger, current_time=now)

    # Oscillation detected but doesn't block (advisory only)
    assert decision.oscillation_detected is True
    assert decision.oscillation_count >= OSCILLATION_THRESHOLD
    # Still allowed because duration met
    assert decision.allowed is True


def test_check_regime_hysteresis_no_oscillation():
    """Test no oscillation when transitions are infrequent."""
    now = datetime.now(timezone.utc)

    # Only 1 transition in window
    ledger = [
        {"regime": "normal", "timestamp": (now - timedelta(seconds=400)).isoformat().replace('+00:00', 'Z'), "duration_s": 100.0},
        {"regime": "heightened", "timestamp": now.isoformat().replace('+00:00', 'Z'), "duration_s": 400.0},  # Current
    ]

    decision = check_regime_hysteresis("normal", ledger, current_time=now)

    assert decision.oscillation_detected is False
    assert decision.oscillation_count < OSCILLATION_THRESHOLD


# ---------- get_hysteresis_metrics Tests ----------


def test_get_hysteresis_metrics_empty_ledger():
    """Test metrics with empty ledger."""
    metrics = get_hysteresis_metrics([])

    assert metrics["current_regime"] == "unknown"
    assert metrics["current_duration_s"] == 0.0
    assert metrics["time_remaining_s"] == 0.0
    assert metrics["hysteresis_active"] is False


def test_get_hysteresis_metrics_hysteresis_active():
    """Test metrics when hysteresis is active (blocking transitions)."""
    ledger = [
        {"regime": "heightened", "timestamp": "2025-01-01T00:00:00Z", "duration_s": 100.0}
    ]
    metrics = get_hysteresis_metrics(ledger)

    assert metrics["current_regime"] == "heightened"
    assert metrics["current_duration_s"] == 100.0
    assert metrics["min_duration_s"] == 300.0
    assert metrics["time_remaining_s"] == 200.0
    assert metrics["hysteresis_active"] is True


def test_get_hysteresis_metrics_hysteresis_inactive():
    """Test metrics when hysteresis is inactive (not blocking)."""
    ledger = [
        {"regime": "heightened", "timestamp": "2025-01-01T00:00:00Z", "duration_s": 400.0}
    ]
    metrics = get_hysteresis_metrics(ledger)

    assert metrics["current_regime"] == "heightened"
    assert metrics["current_duration_s"] == 400.0
    assert metrics["min_duration_s"] == 300.0
    assert metrics["time_remaining_s"] == 0.0
    assert metrics["hysteresis_active"] is False


# ---------- stabilize_recovery_ramp Tests ----------


def test_stabilize_recovery_ramp_premature_exit_blocked():
    """Test recovery ramp blocks premature exit to normal when C < threshold."""
    regime, reason = stabilize_recovery_ramp("normal", current_continuity_score=0.70)

    assert regime == "recovery"
    assert "recovery_ramp_stabilization" in reason
    assert "0.70<0.85" in reason


def test_stabilize_recovery_ramp_exit_allowed():
    """Test recovery ramp allows exit when C ≥ threshold."""
    regime, reason = stabilize_recovery_ramp("normal", current_continuity_score=0.90)

    assert regime == "normal"
    assert "recovery_threshold_met" in reason
    assert "0.90>=0.85" in reason


def test_stabilize_recovery_ramp_exact_threshold():
    """Test recovery ramp at exact threshold boundary."""
    regime, reason = stabilize_recovery_ramp("normal", current_continuity_score=0.85)

    assert regime == "normal"
    assert "recovery_threshold_met" in reason


def test_stabilize_recovery_ramp_non_normal_transition():
    """Test recovery ramp doesn't block non-normal transitions."""
    # Recovery → heightened should pass through
    regime, reason = stabilize_recovery_ramp("heightened", current_continuity_score=0.50)

    assert regime == "heightened"
    assert "no_recovery_stabilization_needed" in reason


def test_stabilize_recovery_ramp_custom_threshold():
    """Test recovery ramp with custom threshold."""
    regime, reason = stabilize_recovery_ramp("normal", current_continuity_score=0.80, recovery_threshold=0.90)

    assert regime == "recovery"  # Blocked (0.80 < 0.90)


# ---------- Edge Cases ----------


def test_check_regime_hysteresis_exact_minimum_duration():
    """Test hysteresis at exact minimum duration boundary."""
    # Heightened requires exactly 300s
    ledger = [
        {"regime": "heightened", "timestamp": "2025-01-01T00:00:00Z", "duration_s": 300.0}
    ]
    decision = check_regime_hysteresis("normal", ledger)

    # Exactly at minimum should allow transition
    assert decision.allowed is True
    assert decision.time_remaining_s == 0.0


def test_check_regime_hysteresis_just_below_minimum():
    """Test hysteresis just below minimum duration."""
    # Heightened requires 300s, been 299.9s
    ledger = [
        {"regime": "heightened", "timestamp": "2025-01-01T00:00:00Z", "duration_s": 299.9}
    ]
    decision = check_regime_hysteresis("normal", ledger)

    # Just below minimum should block
    assert decision.allowed is False
    assert decision.time_remaining_s == pytest.approx(0.1, abs=0.01)


def test_check_regime_hysteresis_just_above_minimum():
    """Test hysteresis just above minimum duration."""
    # Heightened requires 300s, been 300.1s
    ledger = [
        {"regime": "heightened", "timestamp": "2025-01-01T00:00:00Z", "duration_s": 300.1}
    ]
    decision = check_regime_hysteresis("normal", ledger)

    # Just above minimum should allow
    assert decision.allowed is True
    assert decision.time_remaining_s == 0.0


def test_check_regime_hysteresis_unknown_regime_default():
    """Test hysteresis with unknown regime uses default 60s."""
    ledger = [
        {"regime": "unknown_regime", "timestamp": "2025-01-01T00:00:00Z", "duration_s": 50.0}
    ]
    decision = check_regime_hysteresis("normal", ledger)

    # Unknown regime should use default 60s minimum
    assert decision.allowed is False
    assert decision.min_duration_s == 60.0
    assert decision.time_remaining_s == 10.0


# ---------- Constraint Verification Tests ----------


def test_hysteresis_decision_structure():
    """Test HysteresisDecision has expected structure."""
    ledger = [
        {"regime": "heightened", "timestamp": "2025-01-01T00:00:00Z", "duration_s": 100.0}
    ]
    decision = check_regime_hysteresis("normal", ledger)

    assert hasattr(decision, "allowed")
    assert hasattr(decision, "effective_regime")
    assert hasattr(decision, "reason")
    assert hasattr(decision, "current_regime")
    assert hasattr(decision, "current_duration_s")
    assert hasattr(decision, "min_duration_s")
    assert hasattr(decision, "time_remaining_s")
    assert hasattr(decision, "oscillation_detected")
    assert hasattr(decision, "oscillation_count")


def test_hysteresis_pure_function():
    """Test hysteresis check is pure (no ledger mutation)."""
    ledger = [
        {"regime": "heightened", "timestamp": "2025-01-01T00:00:00Z", "duration_s": 100.0}
    ]
    ledger_copy = ledger.copy()

    check_regime_hysteresis("normal", ledger)

    # Ledger should be unchanged
    assert ledger == ledger_copy


def test_hysteresis_time_remaining_always_nonnegative():
    """Test time_remaining_s is always ≥ 0.0."""
    # Case 1: Duration < minimum
    ledger = [
        {"regime": "heightened", "timestamp": "2025-01-01T00:00:00Z", "duration_s": 100.0}
    ]
    decision = check_regime_hysteresis("normal", ledger)
    assert decision.time_remaining_s >= 0.0

    # Case 2: Duration ≥ minimum
    ledger = [
        {"regime": "heightened", "timestamp": "2025-01-01T00:00:00Z", "duration_s": 400.0}
    ]
    decision = check_regime_hysteresis("normal", ledger)
    assert decision.time_remaining_s == 0.0


def test_hysteresis_effective_regime_valid():
    """Test effective_regime is always a valid regime name."""
    valid_regimes = ["normal", "heightened", "controlled_degradation", "emergency_stabilization", "recovery"]

    ledger = [
        {"regime": "heightened", "timestamp": "2025-01-01T00:00:00Z", "duration_s": 100.0}
    ]
    decision = check_regime_hysteresis("normal", ledger)

    # effective_regime should be current (blocked) or proposed (allowed)
    assert decision.effective_regime in ["heightened", "normal"]


# ---------- Scenario Tests ----------


def test_scenario_normal_heightened_thrash_prevented():
    """Test NORMAL ↔ HEIGHTENED thrash is prevented by hysteresis."""
    # Scenario: System tries to switch NORMAL → HEIGHTENED → NORMAL rapidly

    # Start in normal, been 70s (> 60s minimum)
    ledger = [
        {"regime": "normal", "timestamp": "2025-01-01T00:00:00Z", "duration_s": 70.0}
    ]
    decision1 = check_regime_hysteresis("heightened", ledger)
    assert decision1.allowed is True  # Allowed to switch to heightened

    # Now in heightened, only been 10s (< 300s minimum)
    ledger.append({"regime": "heightened", "timestamp": "2025-01-01T00:01:10Z", "duration_s": 10.0})
    decision2 = check_regime_hysteresis("normal", ledger)
    assert decision2.allowed is False  # BLOCKED - thrash prevented
    assert decision2.effective_regime == "heightened"


def test_scenario_recovery_premature_exit_blocked():
    """Test recovery → normal premature exit is blocked."""
    # Scenario: System in recovery, tries to exit with low C

    # Recovery for 2000s (> 1800s minimum), but C too low
    regime, reason = stabilize_recovery_ramp("normal", current_continuity_score=0.70)
    assert regime == "recovery"  # Blocked despite duration met


def test_scenario_emergency_persistence_enforced():
    """Test emergency regime persists for full 900s."""
    # Scenario: Emergency triggered, tries to exit early

    # Emergency for only 500s (< 900s minimum)
    ledger = [
        {"regime": "emergency_stabilization", "timestamp": "2025-01-01T00:00:00Z", "duration_s": 500.0}
    ]
    decision = check_regime_hysteresis("recovery", ledger)
    assert decision.allowed is False
    assert decision.time_remaining_s == 400.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
