"""Unit tests for Continuity Proofs - Phase 13

Tests for continuity_proof.py: ledger continuity, temporal continuity,
amplitude continuity, and regime continuity proofs.

Per Phase13_Implementation_Checklist.md: 8 tests required.
"""

import pytest

from src.nova.continuity.avl_ledger import AVLEntry
from src.nova.continuity.continuity_proof import (
    ContinuityProof,
    ProofResult,
    get_continuity_proof,
    reset_continuity_proof,
    DEFAULT_AMPLITUDE_DELTA,
)


# ---------- Fixtures ----------


@pytest.fixture
def proof():
    """Create continuity proof validator."""
    return ContinuityProof()


@pytest.fixture
def valid_ledger():
    """Create valid ledger with proper continuity."""
    return [
        AVLEntry(
            timestamp="2025-01-01T12:00:00+00:00",
            elapsed_s=0.0,
            orp_regime="normal",
            orp_regime_score=0.15,
            contributing_factors={"urf_composite_risk": 0.15},
            posture_adjustments={"threshold_multiplier": 1.0, "traffic_limit": 1.0},
            oracle_regime="normal",
            oracle_regime_score=0.15,
            hysteresis_enforced=True,
            min_duration_enforced=True,
            ledger_continuity=True,
            amplitude_valid=True,
        ),
        AVLEntry(
            timestamp="2025-01-01T12:05:00+00:00",
            elapsed_s=300.0,
            orp_regime="heightened",
            orp_regime_score=0.35,
            contributing_factors={"urf_composite_risk": 0.35},
            posture_adjustments={"threshold_multiplier": 0.85, "traffic_limit": 0.90},
            oracle_regime="heightened",
            oracle_regime_score=0.35,
            transition_from="normal",  # Correct: matches previous regime
            time_in_previous_regime_s=300.0,
            hysteresis_enforced=True,
            min_duration_enforced=True,
            ledger_continuity=True,
            amplitude_valid=True,
        ),
        AVLEntry(
            timestamp="2025-01-01T12:10:00+00:00",
            elapsed_s=600.0,
            orp_regime="heightened",
            orp_regime_score=0.40,
            contributing_factors={"urf_composite_risk": 0.40},
            posture_adjustments={"threshold_multiplier": 0.85, "traffic_limit": 0.90},
            oracle_regime="heightened",
            oracle_regime_score=0.40,
            transition_from=None,  # No transition
            hysteresis_enforced=True,
            min_duration_enforced=True,
            ledger_continuity=True,
            amplitude_valid=True,
        ),
    ]


@pytest.fixture
def broken_ledger_continuity():
    """Create ledger with broken ledger continuity."""
    return [
        AVLEntry(
            timestamp="2025-01-01T12:00:00+00:00",
            elapsed_s=0.0,
            orp_regime="normal",
            orp_regime_score=0.15,
            contributing_factors={"urf_composite_risk": 0.15},
            posture_adjustments={"threshold_multiplier": 1.0, "traffic_limit": 1.0},
            oracle_regime="normal",
            hysteresis_enforced=True,
            min_duration_enforced=True,
        ),
        AVLEntry(
            timestamp="2025-01-01T12:05:00+00:00",
            elapsed_s=300.0,
            orp_regime="heightened",
            orp_regime_score=0.35,
            contributing_factors={"urf_composite_risk": 0.35},
            posture_adjustments={"threshold_multiplier": 0.85, "traffic_limit": 0.90},
            oracle_regime="heightened",
            transition_from="controlled_degradation",  # Wrong! Should be "normal"
            hysteresis_enforced=True,
            min_duration_enforced=True,
        ),
    ]


@pytest.fixture
def broken_temporal_continuity():
    """Create ledger with broken temporal continuity."""
    return [
        AVLEntry(
            timestamp="2025-01-01T12:05:00+00:00",  # Later timestamp first
            elapsed_s=300.0,
            orp_regime="normal",
            orp_regime_score=0.15,
            contributing_factors={"urf_composite_risk": 0.15},
            posture_adjustments={"threshold_multiplier": 1.0, "traffic_limit": 1.0},
            oracle_regime="normal",
            hysteresis_enforced=True,
            min_duration_enforced=True,
        ),
        AVLEntry(
            timestamp="2025-01-01T12:00:00+00:00",  # Earlier timestamp second!
            elapsed_s=0.0,  # Also out of order
            orp_regime="normal",
            orp_regime_score=0.16,
            contributing_factors={"urf_composite_risk": 0.16},
            posture_adjustments={"threshold_multiplier": 1.0, "traffic_limit": 1.0},
            oracle_regime="normal",
            hysteresis_enforced=True,
            min_duration_enforced=True,
        ),
    ]


@pytest.fixture
def broken_amplitude_continuity():
    """Create ledger with broken amplitude continuity."""
    return [
        AVLEntry(
            timestamp="2025-01-01T12:00:00+00:00",
            elapsed_s=0.0,
            orp_regime="normal",
            orp_regime_score=0.15,
            contributing_factors={"urf_composite_risk": 0.15},
            posture_adjustments={"threshold_multiplier": 1.0, "traffic_limit": 1.0},
            oracle_regime="normal",
            hysteresis_enforced=True,
            min_duration_enforced=True,
        ),
        AVLEntry(
            timestamp="2025-01-01T12:05:00+00:00",
            elapsed_s=300.0,
            orp_regime="emergency_stabilization",
            orp_regime_score=0.75,
            contributing_factors={"urf_composite_risk": 0.75},
            posture_adjustments={
                "threshold_multiplier": 0.3,  # Jump from 1.0 to 0.3 (delta=0.7 > 0.5)
                "traffic_limit": 0.2,  # Jump from 1.0 to 0.2 (delta=0.8 > 0.5)
            },
            oracle_regime="emergency_stabilization",
            hysteresis_enforced=True,
            min_duration_enforced=True,
        ),
    ]


@pytest.fixture
def broken_regime_continuity():
    """Create ledger with broken regime continuity (invariant violations)."""
    return [
        AVLEntry(
            timestamp="2025-01-01T12:00:00+00:00",
            elapsed_s=0.0,
            orp_regime="normal",
            orp_regime_score=0.15,
            contributing_factors={"urf_composite_risk": 0.15},
            posture_adjustments={"threshold_multiplier": 1.0, "traffic_limit": 1.0},
            oracle_regime="normal",
            hysteresis_enforced=False,  # Violation!
            min_duration_enforced=True,
        ),
        AVLEntry(
            timestamp="2025-01-01T12:05:00+00:00",
            elapsed_s=300.0,
            orp_regime="heightened",
            orp_regime_score=0.35,
            contributing_factors={"urf_composite_risk": 0.35},
            posture_adjustments={"threshold_multiplier": 0.85, "traffic_limit": 0.90},
            oracle_regime="heightened",
            hysteresis_enforced=True,
            min_duration_enforced=False,  # Violation!
        ),
    ]


# ---------- Test 1: Ledger Continuity Proof Pass ----------


def test_ledger_continuity_proof_pass(proof, valid_ledger):
    """Test valid ledger passes ledger continuity proof."""
    result = proof.prove_ledger_continuity(valid_ledger)
    
    assert result.passed is True
    assert result.violations == []
    assert result.proof_name == "ledger_continuity"
    assert result.entries_checked == 3


def test_ledger_continuity_empty_ledger(proof):
    """Test empty ledger passes ledger continuity proof."""
    result = proof.prove_ledger_continuity([])
    
    assert result.passed is True
    assert result.entries_checked == 0


def test_ledger_continuity_single_entry(proof, valid_ledger):
    """Test single entry ledger passes ledger continuity proof."""
    result = proof.prove_ledger_continuity([valid_ledger[0]])
    
    assert result.passed is True
    assert result.entries_checked == 1


# ---------- Test 2: Ledger Continuity Proof Fail ----------


def test_ledger_continuity_proof_fail(proof, broken_ledger_continuity):
    """Test broken continuity is detected."""
    result = proof.prove_ledger_continuity(broken_ledger_continuity)
    
    assert result.passed is False
    assert len(result.violations) == 1
    assert "transition_from=controlled_degradation" in result.violations[0]
    assert "previous regime=normal" in result.violations[0]


# ---------- Test 3: Temporal Continuity Proof Pass ----------


def test_temporal_continuity_proof_pass(proof, valid_ledger):
    """Test monotonic timestamps pass temporal continuity proof."""
    result = proof.prove_temporal_continuity(valid_ledger)
    
    assert result.passed is True
    assert result.violations == []
    assert result.proof_name == "temporal_continuity"


def test_temporal_continuity_empty_ledger(proof):
    """Test empty ledger passes temporal continuity proof."""
    result = proof.prove_temporal_continuity([])
    
    assert result.passed is True


# ---------- Test 4: Temporal Continuity Proof Fail ----------


def test_temporal_continuity_proof_fail(proof, broken_temporal_continuity):
    """Test out-of-order timestamps are detected."""
    result = proof.prove_temporal_continuity(broken_temporal_continuity)
    
    assert result.passed is False
    assert len(result.violations) >= 1
    # Should detect both elapsed_s and timestamp violations
    assert any("elapsed_s" in v for v in result.violations)
    assert any("timestamp" in v for v in result.violations)


# ---------- Test 5: Amplitude Continuity Proof Pass ----------


def test_amplitude_continuity_proof_pass(proof, valid_ledger):
    """Test smooth transitions pass amplitude continuity proof."""
    result = proof.prove_amplitude_continuity(valid_ledger)
    
    assert result.passed is True
    assert result.violations == []
    assert result.proof_name == "amplitude_continuity"


def test_amplitude_continuity_empty_ledger(proof):
    """Test empty ledger passes amplitude continuity proof."""
    result = proof.prove_amplitude_continuity([])
    
    assert result.passed is True


# ---------- Test 6: Amplitude Continuity Proof Fail ----------


def test_amplitude_continuity_proof_fail(proof, broken_amplitude_continuity):
    """Test discontinuous jumps are detected."""
    result = proof.prove_amplitude_continuity(broken_amplitude_continuity)
    
    assert result.passed is False
    assert len(result.violations) >= 1
    # Should detect both threshold_multiplier and traffic_limit jumps
    assert any("threshold_multiplier" in v for v in result.violations)
    assert any("traffic_limit" in v for v in result.violations)


def test_amplitude_continuity_custom_delta(proof, broken_amplitude_continuity):
    """Test custom delta threshold."""
    # With large delta (1.0), the jumps should pass
    result = proof.prove_amplitude_continuity(broken_amplitude_continuity, max_delta=1.0)
    
    assert result.passed is True


# ---------- Test 7: Regime Continuity Proof Pass ----------


def test_regime_continuity_proof_pass(proof, valid_ledger):
    """Test invariants respected passes regime continuity proof."""
    result = proof.prove_regime_continuity(valid_ledger)
    
    assert result.passed is True
    assert result.violations == []
    assert result.proof_name == "regime_continuity"


# ---------- Test 8: Regime Continuity Proof Fail ----------


def test_regime_continuity_proof_fail(proof, broken_regime_continuity):
    """Test invariant violations are detected."""
    result = proof.prove_regime_continuity(broken_regime_continuity)
    
    assert result.passed is False
    assert len(result.violations) == 2
    assert any("hysteresis not enforced" in v for v in result.violations)
    assert any("min-duration not enforced" in v for v in result.violations)


# ---------- Additional Tests ----------


def test_prove_all(proof, valid_ledger):
    """Test prove_all runs all proofs."""
    results = proof.prove_all(valid_ledger)
    
    assert "ledger_continuity" in results
    assert "temporal_continuity" in results
    assert "amplitude_continuity" in results
    assert "regime_continuity" in results
    
    # All should pass for valid ledger
    assert all(r.passed for r in results.values())


def test_prove_all_pass(proof, valid_ledger):
    """Test prove_all_pass returns overall status."""
    all_passed, results = proof.prove_all_pass(valid_ledger)
    
    assert all_passed is True
    assert len(results) == 4


def test_prove_all_with_failures(proof, broken_ledger_continuity):
    """Test prove_all_pass detects failures."""
    all_passed, results = proof.prove_all_pass(broken_ledger_continuity)
    
    assert all_passed is False
    assert results["ledger_continuity"].passed is False


def test_get_summary(proof, valid_ledger):
    """Test get_summary provides correct counts."""
    results = proof.prove_all(valid_ledger)
    summary = proof.get_summary(results)
    
    assert summary["total_proofs"] == 4
    assert summary["passed"] == 4
    assert summary["failed"] == 0
    assert summary["all_passed"] is True
    assert summary["failed_proofs"] == []
    assert summary["total_violations"] == 0


def test_get_summary_with_failures(proof, broken_regime_continuity):
    """Test get_summary with failures."""
    results = proof.prove_all(broken_regime_continuity)
    summary = proof.get_summary(results)
    
    assert summary["failed"] >= 1
    assert summary["all_passed"] is False
    assert len(summary["failed_proofs"]) >= 1
    assert summary["total_violations"] >= 1


def test_proof_result_to_dict(proof, valid_ledger):
    """Test ProofResult serialization."""
    result = proof.prove_ledger_continuity(valid_ledger)
    d = result.to_dict()
    
    assert d["proof_name"] == "ledger_continuity"
    assert d["passed"] is True
    assert d["violations"] == []
    assert d["entries_checked"] == 3


def test_get_continuity_proof_singleton():
    """Test global continuity proof singleton."""
    reset_continuity_proof()
    
    proof1 = get_continuity_proof()
    proof2 = get_continuity_proof()
    
    assert proof1 is proof2
    
    reset_continuity_proof()


def test_amplitude_delta_configurable():
    """Test amplitude delta is configurable."""
    proof_strict = ContinuityProof(amplitude_delta=0.1)
    proof_relaxed = ContinuityProof(amplitude_delta=1.0)
    
    ledger = [
        AVLEntry(
            timestamp="2025-01-01T12:00:00+00:00",
            elapsed_s=0.0,
            orp_regime="normal",
            posture_adjustments={"threshold_multiplier": 1.0, "traffic_limit": 1.0},
            oracle_regime="normal",
            hysteresis_enforced=True,
            min_duration_enforced=True,
        ),
        AVLEntry(
            timestamp="2025-01-01T12:05:00+00:00",
            elapsed_s=300.0,
            orp_regime="heightened",
            posture_adjustments={"threshold_multiplier": 0.7, "traffic_limit": 0.8},
            oracle_regime="heightened",
            hysteresis_enforced=True,
            min_duration_enforced=True,
        ),
    ]
    
    # Strict should fail (delta 0.3 > 0.1)
    result_strict = proof_strict.prove_amplitude_continuity(ledger)
    assert result_strict.passed is False
    
    # Relaxed should pass (delta 0.3 < 1.0)
    result_relaxed = proof_relaxed.prove_amplitude_continuity(ledger)
    assert result_relaxed.passed is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])