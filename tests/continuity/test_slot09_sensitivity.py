"""Unit tests for Slot09 Sensitivity Adapter - Phase 11.3 Step 4"""

import pytest
from src.nova.continuity.slot09_sensitivity import (
    compute_sensitivity_multiplier,
    apply_sensitivity_scaling,
    get_sensitivity_metadata,
    SENSITIVITY_MULTIPLIER_TABLE,
)


# ---------- Canonical Multiplier Table Tests ----------


def test_sensitivity_multiplier_table_structure():
    """Test canonical sensitivity multiplier table has expected structure."""
    # All regimes present
    assert "normal" in SENSITIVITY_MULTIPLIER_TABLE
    assert "heightened" in SENSITIVITY_MULTIPLIER_TABLE
    assert "controlled_degradation" in SENSITIVITY_MULTIPLIER_TABLE
    assert "emergency_stabilization" in SENSITIVITY_MULTIPLIER_TABLE
    assert "recovery" in SENSITIVITY_MULTIPLIER_TABLE

    # All regimes have at least one threshold
    for regime, thresholds in SENSITIVITY_MULTIPLIER_TABLE.items():
        assert len(thresholds) > 0
        # Each threshold is (duration_s, multiplier)
        for threshold_s, multiplier in thresholds:
            assert threshold_s >= 0.0
            assert 1.0 <= multiplier <= 2.0  # Multipliers reduce sensitivity (≥1.0)


def test_sensitivity_multiplier_table_has_zero_threshold():
    """Test all regimes have 0.0 threshold (fallback)."""
    for regime, thresholds in SENSITIVITY_MULTIPLIER_TABLE.items():
        # At least one threshold must be 0.0
        zero_threshold_exists = any(t[0] == 0.0 for t in thresholds)
        assert zero_threshold_exists, f"Regime {regime} missing 0.0 threshold fallback"


# ---------- compute_sensitivity_multiplier Tests ----------


def test_compute_sensitivity_multiplier_normal_always_1_0():
    """Test normal regime always returns 1.0 (no adjustment)."""
    assert compute_sensitivity_multiplier("normal", 0.0) == 1.0
    assert compute_sensitivity_multiplier("normal", 100.0) == 1.0
    assert compute_sensitivity_multiplier("normal", 10000.0) == 1.0


def test_compute_sensitivity_multiplier_heightened_short_duration():
    """Test heightened regime <5min returns 1.05."""
    assert compute_sensitivity_multiplier("heightened", 0.0) == 1.05
    assert compute_sensitivity_multiplier("heightened", 100.0) == 1.05
    assert compute_sensitivity_multiplier("heightened", 299.0) == 1.05


def test_compute_sensitivity_multiplier_heightened_long_duration():
    """Test heightened regime ≥5min returns 1.15."""
    assert compute_sensitivity_multiplier("heightened", 300.0) == 1.15
    assert compute_sensitivity_multiplier("heightened", 400.0) == 1.15
    assert compute_sensitivity_multiplier("heightened", 10000.0) == 1.15


def test_compute_sensitivity_multiplier_controlled_degradation():
    """Test controlled_degradation returns 1.30."""
    assert compute_sensitivity_multiplier("controlled_degradation", 0.0) == 1.30
    assert compute_sensitivity_multiplier("controlled_degradation", 500.0) == 1.30


def test_compute_sensitivity_multiplier_emergency_stabilization():
    """Test emergency_stabilization returns 1.50."""
    assert compute_sensitivity_multiplier("emergency_stabilization", 0.0) == 1.50
    assert compute_sensitivity_multiplier("emergency_stabilization", 100.0) == 1.50


def test_compute_sensitivity_multiplier_recovery():
    """Test recovery returns 1.20 (gradual recovery)."""
    assert compute_sensitivity_multiplier("recovery", 0.0) == 1.20
    assert compute_sensitivity_multiplier("recovery", 1000.0) == 1.20


def test_compute_sensitivity_multiplier_unknown_regime():
    """Test unknown regime defaults to 1.0 (no adjustment)."""
    assert compute_sensitivity_multiplier("unknown", 100.0) == 1.0
    assert compute_sensitivity_multiplier("invalid_regime", 500.0) == 1.0
    assert compute_sensitivity_multiplier("", 100.0) == 1.0


def test_compute_sensitivity_multiplier_case_insensitive():
    """Test regime names are case-insensitive."""
    assert compute_sensitivity_multiplier("NORMAL", 100.0) == 1.0
    assert compute_sensitivity_multiplier("Normal", 100.0) == 1.0
    assert compute_sensitivity_multiplier("NoRmAl", 100.0) == 1.0


def test_compute_sensitivity_multiplier_whitespace_trimmed():
    """Test regime names are trimmed of whitespace."""
    assert compute_sensitivity_multiplier(" normal ", 100.0) == 1.0
    assert compute_sensitivity_multiplier("  heightened  ", 100.0) == 1.05


# ---------- apply_sensitivity_scaling Tests ----------


def test_apply_sensitivity_scaling_normal_no_change():
    """Test normal regime preserves threshold (multiplier=1.0)."""
    assert apply_sensitivity_scaling(0.25, "normal", 100.0) == 0.25
    assert apply_sensitivity_scaling(1.0, "normal", 500.0) == 1.0
    assert apply_sensitivity_scaling(0.5, "normal", 1000.0) == 0.5


def test_apply_sensitivity_scaling_heightened_short():
    """Test heightened <5min scales by 1.05."""
    # 0.25 * 1.05 = 0.2625
    assert apply_sensitivity_scaling(0.25, "heightened", 100.0) == pytest.approx(0.2625)
    # 1.0 * 1.05 = 1.05
    assert apply_sensitivity_scaling(1.0, "heightened", 200.0) == pytest.approx(1.05)


def test_apply_sensitivity_scaling_heightened_long():
    """Test heightened ≥5min scales by 1.15."""
    # 0.25 * 1.15 = 0.2875
    assert apply_sensitivity_scaling(0.25, "heightened", 300.0) == pytest.approx(0.2875)
    # 1.0 * 1.15 = 1.15
    assert apply_sensitivity_scaling(1.0, "heightened", 500.0) == pytest.approx(1.15)


def test_apply_sensitivity_scaling_emergency():
    """Test emergency_stabilization scales by 1.50."""
    # 0.25 * 1.50 = 0.375
    assert apply_sensitivity_scaling(0.25, "emergency_stabilization", 100.0) == pytest.approx(0.375)
    # 1.0 * 1.50 = 1.50
    assert apply_sensitivity_scaling(1.0, "emergency_stabilization", 200.0) == pytest.approx(1.50)


def test_apply_sensitivity_scaling_recovery():
    """Test recovery scales by 1.20 (gradual)."""
    # 0.25 * 1.20 = 0.30
    assert apply_sensitivity_scaling(0.25, "recovery", 100.0) == pytest.approx(0.30)
    # 1.0 * 1.20 = 1.20
    assert apply_sensitivity_scaling(1.0, "recovery", 500.0) == pytest.approx(1.20)


def test_apply_sensitivity_scaling_clamps_to_minimum():
    """Test result never goes below base threshold."""
    # Multiplier should always be ≥1.0, but verify clamping logic
    base = 0.25
    result = apply_sensitivity_scaling(base, "normal", 100.0)
    assert result >= base


def test_apply_sensitivity_scaling_clamps_to_maximum():
    """Test result never exceeds 2x base threshold."""
    # Even if multiplier could be >2.0 (not in our table), verify clamping
    base = 0.25
    max_result = base * 2.0
    # Emergency is 1.50, so should be < 2x
    result = apply_sensitivity_scaling(base, "emergency_stabilization", 100.0)
    assert result <= max_result


def test_apply_sensitivity_scaling_multiplicative_not_additive():
    """Test scaling is multiplicative (threshold * multiplier)."""
    # 0.25 * 1.15 = 0.2875 (not 0.25 + 1.15)
    result = apply_sensitivity_scaling(0.25, "heightened", 300.0)
    assert result == pytest.approx(0.2875)
    assert result != pytest.approx(1.40)  # Would be additive


# ---------- get_sensitivity_metadata Tests ----------


def test_get_sensitivity_metadata_structure():
    """Test metadata has expected structure."""
    metadata = get_sensitivity_metadata("heightened", 100.0)

    assert "regime" in metadata
    assert "duration_s" in metadata
    assert "multiplier" in metadata
    assert "threshold_matched_s" in metadata


def test_get_sensitivity_metadata_normal():
    """Test metadata for normal regime."""
    metadata = get_sensitivity_metadata("normal", 500.0)

    assert metadata["regime"] == "normal"
    assert metadata["duration_s"] == 500.0
    assert metadata["multiplier"] == 1.0
    assert metadata["threshold_matched_s"] == 0.0


def test_get_sensitivity_metadata_heightened_short():
    """Test metadata for heightened <5min."""
    metadata = get_sensitivity_metadata("heightened", 100.0)

    assert metadata["regime"] == "heightened"
    assert metadata["duration_s"] == 100.0
    assert metadata["multiplier"] == 1.05
    assert metadata["threshold_matched_s"] == 0.0  # Matched 0.0 threshold


def test_get_sensitivity_metadata_heightened_long():
    """Test metadata for heightened ≥5min."""
    metadata = get_sensitivity_metadata("heightened", 400.0)

    assert metadata["regime"] == "heightened"
    assert metadata["duration_s"] == 400.0
    assert metadata["multiplier"] == 1.15
    assert metadata["threshold_matched_s"] == 300.0  # Matched 300s threshold


def test_get_sensitivity_metadata_emergency():
    """Test metadata for emergency_stabilization."""
    metadata = get_sensitivity_metadata("emergency_stabilization", 50.0)

    assert metadata["regime"] == "emergency_stabilization"
    assert metadata["multiplier"] == 1.50
    assert metadata["threshold_matched_s"] == 0.0


# ---------- Edge Cases ----------


def test_sensitivity_scaling_zero_threshold():
    """Test threshold=0.0 stays 0.0 regardless of regime."""
    # Edge case: zero threshold should stay zero
    assert apply_sensitivity_scaling(0.0, "normal", 100.0) == 0.0
    assert apply_sensitivity_scaling(0.0, "heightened", 300.0) == 0.0
    assert apply_sensitivity_scaling(0.0, "emergency_stabilization", 50.0) == 0.0


def test_sensitivity_scaling_very_long_duration():
    """Test very long durations use correct threshold."""
    # Heightened stays at 1.15 even after hours
    assert compute_sensitivity_multiplier("heightened", 10000.0) == 1.15
    assert compute_sensitivity_multiplier("heightened", 86400.0) == 1.15  # 24 hours


def test_sensitivity_scaling_exact_threshold_boundary():
    """Test exact threshold boundary (300s) for heightened."""
    # 299.9s should be <5min (1.05)
    assert compute_sensitivity_multiplier("heightened", 299.9) == 1.05
    # 300.0s should be ≥5min (1.15)
    assert compute_sensitivity_multiplier("heightened", 300.0) == 1.15
    # 300.1s should be ≥5min (1.15)
    assert compute_sensitivity_multiplier("heightened", 300.1) == 1.15


# ---------- Constraint Verification Tests ----------


def test_sensitivity_scaling_preserves_threshold_topology():
    """Test scaling only changes magnitude, not detection logic."""
    # This is a conceptual test - in practice, scaling is applied
    # BEFORE detection, so it can't change what is detected.
    # The function only scales thresholds, not detection decisions.

    # Example: stability threshold 0.25 becomes 0.2875 (heightened ≥5min)
    # NOT a different threshold type, just a higher value
    base_threshold = 0.25
    scaled = apply_sensitivity_scaling(base_threshold, "heightened", 300.0)

    # Still a stability threshold, just higher value
    assert scaled == pytest.approx(0.2875)
    assert scaled > base_threshold  # Less sensitive (higher threshold)


def test_sensitivity_scaling_recovery_less_restrictive_than_eta():
    """Test recovery regime is less restrictive than η scaling (1.20 vs 0.25)."""
    # recovery: sensitivity_multiplier=1.20 (moderate threshold increase)
    # recovery: eta_multiplier=0.25 (very restrictive learning)

    # This design choice allows sensitivity to return faster than learning
    assert compute_sensitivity_multiplier("recovery", 100.0) == 1.20
    # Note: eta scaling would be 0.25 for same regime (from eta_scaling.py)


def test_all_multipliers_reduce_sensitivity():
    """Test all multipliers are ≥1.0 (reduce sensitivity, never increase)."""
    for regime, thresholds in SENSITIVITY_MULTIPLIER_TABLE.items():
        for threshold_s, multiplier in thresholds:
            assert multiplier >= 1.0, f"Regime {regime} has multiplier < 1.0: {multiplier}"


def test_sensitivity_scaling_interpretation():
    """Test correct interpretation: higher multiplier = less sensitive."""
    # Base threshold: 0.25 (detect below this stability)
    # Normal: 0.25 * 1.0 = 0.25 (baseline sensitivity)
    # Emergency: 0.25 * 1.50 = 0.375 (higher threshold = less sensitive = fewer detections)

    baseline = apply_sensitivity_scaling(0.25, "normal", 100.0)
    emergency = apply_sensitivity_scaling(0.25, "emergency_stabilization", 100.0)

    # Emergency has higher threshold (less sensitive)
    assert emergency > baseline
    # Emergency detects only more severe cases (stability < 0.375 vs < 0.25)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
