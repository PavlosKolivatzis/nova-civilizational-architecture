"""Unit tests for Emotional Posture Adapter - Phase 11.3 Step 3"""

import pytest
from src.nova.continuity.emotional_posture import (
    compute_emotional_multiplier,
    apply_emotional_constriction,
    get_emotional_posture_metadata,
    EMOTIONAL_MULTIPLIER_TABLE,
)


# ---------- Canonical Multiplier Table Tests ----------


def test_emotional_multiplier_table_structure():
    """Test canonical emotional multiplier table has expected structure."""
    # All regimes present
    assert "normal" in EMOTIONAL_MULTIPLIER_TABLE
    assert "heightened" in EMOTIONAL_MULTIPLIER_TABLE
    assert "controlled_degradation" in EMOTIONAL_MULTIPLIER_TABLE
    assert "emergency_stabilization" in EMOTIONAL_MULTIPLIER_TABLE
    assert "recovery" in EMOTIONAL_MULTIPLIER_TABLE

    # All regimes have at least one threshold
    for regime, thresholds in EMOTIONAL_MULTIPLIER_TABLE.items():
        assert len(thresholds) > 0
        # Each threshold is (duration_s, multiplier)
        for threshold_s, multiplier in thresholds:
            assert threshold_s >= 0.0
            assert 0.0 <= multiplier <= 1.0


def test_emotional_multiplier_table_has_zero_threshold():
    """Test all regimes have 0.0 threshold (fallback)."""
    for regime, thresholds in EMOTIONAL_MULTIPLIER_TABLE.items():
        # At least one threshold must be 0.0
        zero_threshold_exists = any(t[0] == 0.0 for t in thresholds)
        assert zero_threshold_exists, f"Regime {regime} missing 0.0 threshold fallback"


# ---------- compute_emotional_multiplier Tests ----------


def test_compute_emotional_multiplier_normal_always_1_0():
    """Test normal regime always returns 1.0 (no constriction)."""
    assert compute_emotional_multiplier("normal", 0.0) == 1.0
    assert compute_emotional_multiplier("normal", 100.0) == 1.0
    assert compute_emotional_multiplier("normal", 10000.0) == 1.0


def test_compute_emotional_multiplier_heightened_short_duration():
    """Test heightened regime <5min returns 0.95."""
    assert compute_emotional_multiplier("heightened", 0.0) == 0.95
    assert compute_emotional_multiplier("heightened", 100.0) == 0.95
    assert compute_emotional_multiplier("heightened", 299.0) == 0.95


def test_compute_emotional_multiplier_heightened_long_duration():
    """Test heightened regime ≥5min returns 0.85."""
    assert compute_emotional_multiplier("heightened", 300.0) == 0.85
    assert compute_emotional_multiplier("heightened", 400.0) == 0.85
    assert compute_emotional_multiplier("heightened", 10000.0) == 0.85


def test_compute_emotional_multiplier_controlled_degradation():
    """Test controlled_degradation returns 0.70."""
    assert compute_emotional_multiplier("controlled_degradation", 0.0) == 0.70
    assert compute_emotional_multiplier("controlled_degradation", 500.0) == 0.70


def test_compute_emotional_multiplier_emergency_stabilization():
    """Test emergency_stabilization returns 0.50."""
    assert compute_emotional_multiplier("emergency_stabilization", 0.0) == 0.50
    assert compute_emotional_multiplier("emergency_stabilization", 100.0) == 0.50


def test_compute_emotional_multiplier_recovery():
    """Test recovery returns 0.60 (gradual recovery)."""
    assert compute_emotional_multiplier("recovery", 0.0) == 0.60
    assert compute_emotional_multiplier("recovery", 1000.0) == 0.60


def test_compute_emotional_multiplier_unknown_regime():
    """Test unknown regime defaults to 1.0 (no constriction)."""
    assert compute_emotional_multiplier("unknown", 100.0) == 1.0
    assert compute_emotional_multiplier("invalid_regime", 500.0) == 1.0
    assert compute_emotional_multiplier("", 100.0) == 1.0


def test_compute_emotional_multiplier_case_insensitive():
    """Test regime names are case-insensitive."""
    assert compute_emotional_multiplier("NORMAL", 100.0) == 1.0
    assert compute_emotional_multiplier("Normal", 100.0) == 1.0
    assert compute_emotional_multiplier("NoRmAl", 100.0) == 1.0


def test_compute_emotional_multiplier_whitespace_trimmed():
    """Test regime names are trimmed of whitespace."""
    assert compute_emotional_multiplier(" normal ", 100.0) == 1.0
    assert compute_emotional_multiplier("  heightened  ", 100.0) == 0.95


# ---------- apply_emotional_constriction Tests ----------


def test_apply_emotional_constriction_normal_no_change():
    """Test normal regime preserves intensity (multiplier=1.0)."""
    assert apply_emotional_constriction(0.8, "normal", 100.0) == 0.8
    assert apply_emotional_constriction(1.0, "normal", 500.0) == 1.0
    assert apply_emotional_constriction(0.5, "normal", 1000.0) == 0.5


def test_apply_emotional_constriction_heightened_short():
    """Test heightened <5min constricts by 0.95."""
    # 0.8 * 0.95 = 0.76
    assert apply_emotional_constriction(0.8, "heightened", 100.0) == pytest.approx(0.76)
    # 1.0 * 0.95 = 0.95
    assert apply_emotional_constriction(1.0, "heightened", 200.0) == pytest.approx(0.95)


def test_apply_emotional_constriction_heightened_long():
    """Test heightened ≥5min constricts by 0.85."""
    # 0.8 * 0.85 = 0.68
    assert apply_emotional_constriction(0.8, "heightened", 300.0) == pytest.approx(0.68)
    # 1.0 * 0.85 = 0.85
    assert apply_emotional_constriction(1.0, "heightened", 500.0) == pytest.approx(0.85)


def test_apply_emotional_constriction_emergency():
    """Test emergency_stabilization constricts by 0.50."""
    # 0.8 * 0.50 = 0.4
    assert apply_emotional_constriction(0.8, "emergency_stabilization", 100.0) == pytest.approx(0.4)
    # 1.0 * 0.50 = 0.50
    assert apply_emotional_constriction(1.0, "emergency_stabilization", 200.0) == pytest.approx(0.50)


def test_apply_emotional_constriction_recovery():
    """Test recovery constricts by 0.60 (gradual)."""
    # 0.8 * 0.60 = 0.48
    assert apply_emotional_constriction(0.8, "recovery", 100.0) == pytest.approx(0.48)
    # 1.0 * 0.60 = 0.60
    assert apply_emotional_constriction(1.0, "recovery", 500.0) == pytest.approx(0.60)


def test_apply_emotional_constriction_clamps_to_1_0():
    """Test result never exceeds 1.0 even with intensity > 1.0."""
    # 1.2 * 1.0 = 1.2, clamped to 1.0
    assert apply_emotional_constriction(1.2, "normal", 100.0) == 1.0
    # 1.5 * 0.95 = 1.425, clamped to 1.0
    assert apply_emotional_constriction(1.5, "heightened", 100.0) == 1.0


def test_apply_emotional_constriction_clamps_to_0_0():
    """Test result never goes below 0.0."""
    # Negative intensity clamped to 0.0
    assert apply_emotional_constriction(-0.5, "normal", 100.0) == 0.0


def test_apply_emotional_constriction_multiplicative_not_additive():
    """Test constriction is multiplicative (intensity * multiplier)."""
    # 0.6 * 0.85 = 0.51 (not 0.6 + 0.85)
    result = apply_emotional_constriction(0.6, "heightened", 300.0)
    assert result == pytest.approx(0.51)
    assert result != pytest.approx(1.45)  # Would be additive


# ---------- get_emotional_posture_metadata Tests ----------


def test_get_emotional_posture_metadata_structure():
    """Test metadata has expected structure."""
    metadata = get_emotional_posture_metadata("heightened", 100.0)

    assert "regime" in metadata
    assert "duration_s" in metadata
    assert "multiplier" in metadata
    assert "threshold_matched_s" in metadata


def test_get_emotional_posture_metadata_normal():
    """Test metadata for normal regime."""
    metadata = get_emotional_posture_metadata("normal", 500.0)

    assert metadata["regime"] == "normal"
    assert metadata["duration_s"] == 500.0
    assert metadata["multiplier"] == 1.0
    assert metadata["threshold_matched_s"] == 0.0


def test_get_emotional_posture_metadata_heightened_short():
    """Test metadata for heightened <5min."""
    metadata = get_emotional_posture_metadata("heightened", 100.0)

    assert metadata["regime"] == "heightened"
    assert metadata["duration_s"] == 100.0
    assert metadata["multiplier"] == 0.95
    assert metadata["threshold_matched_s"] == 0.0  # Matched 0.0 threshold


def test_get_emotional_posture_metadata_heightened_long():
    """Test metadata for heightened ≥5min."""
    metadata = get_emotional_posture_metadata("heightened", 400.0)

    assert metadata["regime"] == "heightened"
    assert metadata["duration_s"] == 400.0
    assert metadata["multiplier"] == 0.85
    assert metadata["threshold_matched_s"] == 300.0  # Matched 300s threshold


def test_get_emotional_posture_metadata_emergency():
    """Test metadata for emergency_stabilization."""
    metadata = get_emotional_posture_metadata("emergency_stabilization", 50.0)

    assert metadata["regime"] == "emergency_stabilization"
    assert metadata["multiplier"] == 0.50
    assert metadata["threshold_matched_s"] == 0.0


# ---------- Edge Cases ----------


def test_emotional_constriction_zero_intensity():
    """Test intensity=0.0 stays 0.0 regardless of regime."""
    assert apply_emotional_constriction(0.0, "normal", 100.0) == 0.0
    assert apply_emotional_constriction(0.0, "heightened", 300.0) == 0.0
    assert apply_emotional_constriction(0.0, "emergency_stabilization", 50.0) == 0.0


def test_emotional_constriction_very_long_duration():
    """Test very long durations use correct threshold."""
    # Heightened stays at 0.85 even after hours
    assert compute_emotional_multiplier("heightened", 10000.0) == 0.85
    assert compute_emotional_multiplier("heightened", 86400.0) == 0.85  # 24 hours


def test_emotional_constriction_exact_threshold_boundary():
    """Test exact threshold boundary (300s) for heightened."""
    # 299.9s should be <5min (0.95)
    assert compute_emotional_multiplier("heightened", 299.9) == 0.95
    # 300.0s should be ≥5min (0.85)
    assert compute_emotional_multiplier("heightened", 300.0) == 0.85
    # 300.1s should be ≥5min (0.85)
    assert compute_emotional_multiplier("heightened", 300.1) == 0.85


# ---------- Constraint Verification Tests ----------


def test_emotional_constriction_preserves_topology():
    """Test constriction only scales magnitude, not which emotion."""
    # This is a conceptual test - in practice, constriction is applied
    # AFTER emotion selection, so it can't change which emotion is active.
    # The function only scales intensity, not valence or type.

    # Example: joy at 0.8 becomes joy at 0.68 (heightened ≥5min)
    # NOT sadness, NOT neutral - just scaled joy
    joy_intensity = 0.8
    constricted = apply_emotional_constriction(joy_intensity, "heightened", 300.0)

    # Still joy, just lower intensity
    assert constricted == pytest.approx(0.68)
    assert constricted > 0.0  # Not zero (still present)
    assert constricted < joy_intensity  # Reduced, not amplified


def test_emotional_constriction_recovery_more_permissive_than_eta():
    """Test recovery regime is more permissive than η scaling (0.60 vs 0.25)."""
    # recovery: emotional_multiplier=0.60 (allows more emotional expression)
    # recovery: eta_multiplier=0.25 (very restrictive learning)

    # This design choice allows emotional recovery faster than learning recovery
    assert compute_emotional_multiplier("recovery", 100.0) == 0.60
    # Note: eta scaling would be 0.25 for same regime (from eta_scaling.py)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
