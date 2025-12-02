"""Unit tests for Drift Guard - Phase 13

Tests for drift_guard.py: drift detection rules, configuration,
and response strategies.

Per Phase13_Implementation_Checklist.md: 10 tests required.
"""

import pytest

from src.nova.continuity.avl_ledger import AVLEntry
from src.nova.continuity.drift_guard import (
    DriftGuard,
    DriftDetectedError,
    DriftResult,
    get_drift_guard,
    reset_drift_guard,
    SCORE_DRIFT_THRESHOLD,
    AMPLITUDE_BOUNDS,
)


# ---------- Fixtures ----------


@pytest.fixture
def drift_guard():
    """Create drift guard for testing."""
    return DriftGuard()


@pytest.fixture
def valid_entry():
    """Create valid AVL entry (no drift)."""
    return AVLEntry(
        timestamp="2025-01-01T12:00:00+00:00",
        orp_regime="normal",
        orp_regime_score=0.15,
        contributing_factors={"urf_composite_risk": 0.15},
        posture_adjustments={
            "threshold_multiplier": 1.0,
            "traffic_limit": 1.0,
        },
        oracle_regime="normal",
        oracle_regime_score=0.15,
        dual_modality_agreement=True,
        hysteresis_enforced=True,
        min_duration_enforced=True,
        ledger_continuity=True,
        amplitude_valid=True,
    )


@pytest.fixture
def dual_modality_drift_entry():
    """Create entry with dual-modality disagreement."""
    return AVLEntry(
        timestamp="2025-01-01T12:00:00+00:00",
        orp_regime="heightened",
        orp_regime_score=0.35,
        contributing_factors={"urf_composite_risk": 0.35},
        posture_adjustments={
            "threshold_multiplier": 0.85,
            "traffic_limit": 0.90,
        },
        oracle_regime="normal",  # Disagreement!
        oracle_regime_score=0.35,
        dual_modality_agreement=False,
        hysteresis_enforced=True,
        min_duration_enforced=True,
        ledger_continuity=True,
        amplitude_valid=True,
    )


@pytest.fixture
def score_drift_entry():
    """Create entry with score computation drift."""
    return AVLEntry(
        timestamp="2025-01-01T12:00:00+00:00",
        orp_regime="normal",
        orp_regime_score=0.15,
        contributing_factors={"urf_composite_risk": 0.15},
        posture_adjustments={
            "threshold_multiplier": 1.0,
            "traffic_limit": 1.0,
        },
        oracle_regime="normal",
        oracle_regime_score=0.16,  # Score drift!
        dual_modality_agreement=True,
        hysteresis_enforced=True,
        min_duration_enforced=True,
        ledger_continuity=True,
        amplitude_valid=True,
    )


@pytest.fixture
def invariant_violation_entry():
    """Create entry with invariant violation."""
    return AVLEntry(
        timestamp="2025-01-01T12:00:00+00:00",
        orp_regime="normal",
        orp_regime_score=0.15,
        contributing_factors={"urf_composite_risk": 0.15},
        posture_adjustments={
            "threshold_multiplier": 1.0,
            "traffic_limit": 1.0,
        },
        oracle_regime="normal",
        oracle_regime_score=0.15,
        dual_modality_agreement=True,
        hysteresis_enforced=False,  # Violation!
        min_duration_enforced=True,
        ledger_continuity=True,
        amplitude_valid=True,
    )


@pytest.fixture
def amplitude_bounds_entry():
    """Create entry with amplitude out of bounds."""
    return AVLEntry(
        timestamp="2025-01-01T12:00:00+00:00",
        orp_regime="normal",
        orp_regime_score=0.15,
        contributing_factors={"urf_composite_risk": 0.15},
        posture_adjustments={
            "threshold_multiplier": 3.0,  # Out of bounds! (max 2.0)
            "traffic_limit": 1.0,
        },
        oracle_regime="normal",
        oracle_regime_score=0.15,
        dual_modality_agreement=True,
        hysteresis_enforced=True,
        min_duration_enforced=True,
        ledger_continuity=True,
        amplitude_valid=True,
    )


# ---------- Test 1: Dual-Modality Drift Detected ----------


def test_dual_modality_drift_detected(drift_guard, dual_modality_drift_entry):
    """Test ORP ≠ oracle triggers drift."""
    drift_detected, reasons = drift_guard.check(dual_modality_drift_entry)

    assert drift_detected is True
    assert len(reasons) >= 1
    assert any("Dual-modality disagreement" in r for r in reasons)
    assert "ORP=heightened" in reasons[0]
    assert "Oracle=normal" in reasons[0]


# ---------- Test 2: Invariant Violation Drift ----------


def test_invariant_violation_drift(drift_guard, invariant_violation_entry):
    """Test failed invariant triggers drift."""
    drift_detected, reasons = drift_guard.check(invariant_violation_entry)

    assert drift_detected is True
    assert any("hysteresis not enforced" in r for r in reasons)


def test_multiple_invariant_violations(drift_guard):
    """Test multiple invariant violations are all reported."""
    entry = AVLEntry(
        timestamp="2025-01-01T12:00:00+00:00",
        orp_regime="normal",
        orp_regime_score=0.15,
        contributing_factors={"urf_composite_risk": 0.15},
        posture_adjustments={"threshold_multiplier": 1.0, "traffic_limit": 1.0},
        oracle_regime="normal",
        oracle_regime_score=0.15,
        hysteresis_enforced=False,  # Violation 1
        min_duration_enforced=False,  # Violation 2
        ledger_continuity=False,  # Violation 3
        amplitude_valid=False,  # Violation 4
    )

    drift_detected, reasons = drift_guard.check(entry)

    assert drift_detected is True
    assert len(reasons) == 4
    assert any("hysteresis" in r for r in reasons)
    assert any("min-duration" in r for r in reasons)
    assert any("ledger continuity" in r for r in reasons)
    assert any("amplitude invalid" in r for r in reasons)


# ---------- Test 3: Amplitude Bounds Drift ----------


def test_amplitude_bounds_drift(drift_guard, amplitude_bounds_entry):
    """Test out-of-bounds amplitude triggers drift."""
    drift_detected, reasons = drift_guard.check(amplitude_bounds_entry)

    assert drift_detected is True
    assert any("threshold_multiplier" in r for r in reasons)
    assert any("out of bounds" in r.lower() for r in reasons)


def test_amplitude_bounds_traffic_limit(drift_guard):
    """Test traffic_limit out of bounds triggers drift."""
    entry = AVLEntry(
        timestamp="2025-01-01T12:00:00+00:00",
        orp_regime="normal",
        orp_regime_score=0.15,
        contributing_factors={"urf_composite_risk": 0.15},
        posture_adjustments={
            "threshold_multiplier": 1.0,
            "traffic_limit": 1.5,  # Out of bounds! (max 1.0)
        },
        oracle_regime="normal",
        oracle_regime_score=0.15,
        hysteresis_enforced=True,
        min_duration_enforced=True,
        ledger_continuity=True,
        amplitude_valid=True,
    )

    drift_detected, reasons = drift_guard.check(entry)

    assert drift_detected is True
    assert any("traffic_limit" in r for r in reasons)


# ---------- Test 4: Score Drift Detected ----------


def test_score_drift_detected(drift_guard, score_drift_entry):
    """Test score mismatch triggers drift."""
    drift_detected, reasons = drift_guard.check(score_drift_entry)

    assert drift_detected is True
    assert any("Score drift" in r for r in reasons)


def test_score_drift_within_threshold(drift_guard):
    """Test score difference within threshold does not trigger drift."""
    entry = AVLEntry(
        timestamp="2025-01-01T12:00:00+00:00",
        orp_regime="normal",
        orp_regime_score=0.15,
        contributing_factors={"urf_composite_risk": 0.15},
        posture_adjustments={"threshold_multiplier": 1.0, "traffic_limit": 1.0},
        oracle_regime="normal",
        oracle_regime_score=0.15 + 1e-7,  # Within threshold
        hysteresis_enforced=True,
        min_duration_enforced=True,
        ledger_continuity=True,
        amplitude_valid=True,
    )

    drift_detected, reasons = drift_guard.check(entry)

    assert drift_detected is False
    assert len(reasons) == 0


# ---------- Test 5: No Drift on Valid Entry ----------


def test_no_drift_on_valid_entry(drift_guard, valid_entry):
    """Test no false positives on valid entry."""
    drift_detected, reasons = drift_guard.check(valid_entry)

    assert drift_detected is False
    assert reasons == []


# ---------- Test 6: Drift Reasons Accurate ----------


def test_drift_reasons_accurate(drift_guard, dual_modality_drift_entry):
    """Test reason messages are correct and informative."""
    drift_detected, reasons = drift_guard.check(dual_modality_drift_entry)

    assert drift_detected is True
    # Reason should contain both regimes
    reason = reasons[0]
    assert "heightened" in reason
    assert "normal" in reason


# ---------- Test 7: Halt on Drift Configurable ----------


def test_halt_on_drift_configurable(dual_modality_drift_entry):
    """Test halt setting works."""
    # Default: no halt
    guard = DriftGuard(halt_on_drift=False)
    drift_detected, reasons = guard.check(dual_modality_drift_entry)
    assert drift_detected is True  # Detected but no exception

    # With halt
    guard_halt = DriftGuard(halt_on_drift=True)
    with pytest.raises(DriftDetectedError) as exc_info:
        guard_halt.check(dual_modality_drift_entry)

    assert "Dual-modality disagreement" in str(exc_info.value)
    assert exc_info.value.entry == dual_modality_drift_entry


def test_halt_on_drift_via_configure(dual_modality_drift_entry):
    """Test halt can be configured after creation."""
    guard = DriftGuard(halt_on_drift=False)

    # Configure to halt
    guard.configure(halt_on_drift=True)

    with pytest.raises(DriftDetectedError):
        guard.check(dual_modality_drift_entry)


# ---------- Test 8: Multiple Drift Reasons ----------


def test_multiple_drift_reasons(drift_guard):
    """Test multiple violations are all reported."""
    entry = AVLEntry(
        timestamp="2025-01-01T12:00:00+00:00",
        orp_regime="heightened",  # Disagreement
        orp_regime_score=0.35,
        contributing_factors={"urf_composite_risk": 0.35},
        posture_adjustments={
            "threshold_multiplier": 3.0,  # Out of bounds
            "traffic_limit": 1.0,
        },
        oracle_regime="normal",  # Disagreement
        oracle_regime_score=0.36,  # Score drift
        hysteresis_enforced=False,  # Invariant violation
        min_duration_enforced=True,
        ledger_continuity=True,
        amplitude_valid=True,
    )

    drift_detected, reasons = drift_guard.check(entry)

    assert drift_detected is True
    assert len(reasons) >= 3  # At least 3 violations
    assert any("Dual-modality" in r for r in reasons)
    assert any("Score drift" in r for r in reasons)
    assert any("threshold_multiplier" in r for r in reasons)


# ---------- Test 9: Drift Threshold Tunable ----------


def test_drift_threshold_tunable():
    """Test score drift threshold is adjustable."""
    entry = AVLEntry(
        timestamp="2025-01-01T12:00:00+00:00",
        orp_regime="normal",
        orp_regime_score=0.15,
        contributing_factors={"urf_composite_risk": 0.15},
        posture_adjustments={"threshold_multiplier": 1.0, "traffic_limit": 1.0},
        oracle_regime="normal",
        oracle_regime_score=0.16,  # 0.01 difference
        hysteresis_enforced=True,
        min_duration_enforced=True,
        ledger_continuity=True,
        amplitude_valid=True,
    )

    # Default threshold (1e-6) - should detect drift
    guard_strict = DriftGuard(score_drift_threshold=1e-6)
    drift_detected, _ = guard_strict.check(entry)
    assert drift_detected is True

    # Relaxed threshold (0.1) - should not detect drift
    guard_relaxed = DriftGuard(score_drift_threshold=0.1)
    drift_detected, _ = guard_relaxed.check(entry)
    assert drift_detected is False


def test_drift_threshold_via_configure():
    """Test threshold can be configured after creation."""
    entry = AVLEntry(
        timestamp="2025-01-01T12:00:00+00:00",
        orp_regime="normal",
        orp_regime_score=0.15,
        contributing_factors={"urf_composite_risk": 0.15},
        posture_adjustments={"threshold_multiplier": 1.0, "traffic_limit": 1.0},
        oracle_regime="normal",
        oracle_regime_score=0.16,
        hysteresis_enforced=True,
        min_duration_enforced=True,
        ledger_continuity=True,
        amplitude_valid=True,
    )

    guard = DriftGuard(score_drift_threshold=1e-6)

    # Initially detects drift
    drift_detected, _ = guard.check(entry)
    assert drift_detected is True

    # Relax threshold
    guard.configure(score_drift_threshold=0.1)
    drift_detected, _ = guard.check(entry)
    assert drift_detected is False


# ---------- Test 10: Drift Guard Disabled ----------


def test_drift_guard_disabled(dual_modality_drift_entry):
    """Test drift detection can be disabled."""
    guard = DriftGuard(enabled=False)

    drift_detected, reasons = guard.check(dual_modality_drift_entry)

    assert drift_detected is False
    assert reasons == []


def test_drift_guard_disable_via_configure(dual_modality_drift_entry):
    """Test drift detection can be disabled via configure."""
    guard = DriftGuard(enabled=True)

    # Initially detects drift
    drift_detected, _ = guard.check(dual_modality_drift_entry)
    assert drift_detected is True

    # Disable
    guard.configure(enabled=False)
    drift_detected, _ = guard.check(dual_modality_drift_entry)
    assert drift_detected is False


# ---------- Additional Tests ----------


def test_check_and_update(drift_guard, dual_modality_drift_entry):
    """Test check_and_update updates entry fields."""
    # Entry starts with no drift info
    assert dual_modality_drift_entry.drift_detected is False
    assert dual_modality_drift_entry.drift_reasons == []

    # Check and update
    updated = drift_guard.check_and_update(dual_modality_drift_entry)

    assert updated.drift_detected is True
    assert len(updated.drift_reasons) > 0
    assert updated.dual_modality_agreement is False


def test_drift_result_to_dict(drift_guard, dual_modality_drift_entry):
    """Test DriftResult serialization."""
    drift_detected, reasons = drift_guard.check(dual_modality_drift_entry)

    result = DriftResult(
        drift_detected=drift_detected,
        reasons=reasons,
        entry=dual_modality_drift_entry,
    )

    d = result.to_dict()
    assert d["drift_detected"] is True
    assert len(d["reasons"]) > 0
    assert d["timestamp"] == "2025-01-01T12:00:00+00:00"


def test_get_drift_guard_singleton():
    """Test global drift guard singleton."""
    reset_drift_guard()

    guard1 = get_drift_guard()
    guard2 = get_drift_guard()

    assert guard1 is guard2

    reset_drift_guard()


def test_drift_guard_properties(drift_guard):
    """Test drift guard property accessors."""
    assert drift_guard.halt_on_drift is False
    assert drift_guard.enabled is True
    assert drift_guard.score_drift_threshold == SCORE_DRIFT_THRESHOLD


def test_drift_detected_error_attributes(dual_modality_drift_entry):
    """Test DriftDetectedError has correct attributes."""
    guard = DriftGuard(halt_on_drift=True)

    with pytest.raises(DriftDetectedError) as exc_info:
        guard.check(dual_modality_drift_entry)

    error = exc_info.value
    assert error.entry == dual_modality_drift_entry
    assert len(error.reasons) > 0
    assert "Dual-modality" in error.reasons[0]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
