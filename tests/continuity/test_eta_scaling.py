"""Unit tests for Eta (η) Scaling Adapter - Phase 11.3 Step 2"""

import pytest
from src.nova.continuity.eta_scaling import (
    compute_eta_scale,
    apply_eta_scaling,
    get_eta_scaling_metadata,
    ETA_SCALING_TABLE,
)


# ---------- Canonical Scaling Table Tests ----------


def test_eta_scaling_table_structure():
    """Test canonical η scaling table has expected structure."""
    # All regimes present
    assert "normal" in ETA_SCALING_TABLE
    assert "heightened" in ETA_SCALING_TABLE
    assert "controlled_degradation" in ETA_SCALING_TABLE
    assert "emergency_stabilization" in ETA_SCALING_TABLE
    assert "recovery" in ETA_SCALING_TABLE

    # All regimes have at least one threshold
    for regime, thresholds in ETA_SCALING_TABLE.items():
        assert len(thresholds) > 0
        # Each threshold is (duration_s, scale_factor)
        for threshold_s, scale_factor in thresholds:
            assert threshold_s >= 0.0
            assert 0.0 <= scale_factor <= 1.0


def test_eta_scaling_table_has_zero_threshold():
    """Test all regimes have 0.0 threshold (fallback)."""
    for regime, thresholds in ETA_SCALING_TABLE.items():
        # At least one threshold must be 0.0
        zero_threshold_exists = any(t[0] == 0.0 for t in thresholds)
        assert zero_threshold_exists, f"Regime {regime} missing 0.0 threshold fallback"


# ---------- compute_eta_scale Tests ----------


def test_compute_eta_scale_normal_always_1_0():
    """Test normal regime always returns 1.0."""
    assert compute_eta_scale("normal", 0.0) == 1.0
    assert compute_eta_scale("normal", 100.0) == 1.0
    assert compute_eta_scale("normal", 10000.0) == 1.0


def test_compute_eta_scale_heightened_short_duration():
    """Test heightened regime <5min returns 0.95."""
    assert compute_eta_scale("heightened", 0.0) == 0.95
    assert compute_eta_scale("heightened", 100.0) == 0.95
    assert compute_eta_scale("heightened", 299.0) == 0.95


def test_compute_eta_scale_heightened_long_duration():
    """Test heightened regime ≥5min returns 0.90."""
    assert compute_eta_scale("heightened", 300.0) == 0.90
    assert compute_eta_scale("heightened", 400.0) == 0.90
    assert compute_eta_scale("heightened", 10000.0) == 0.90


def test_compute_eta_scale_controlled_degradation():
    """Test controlled_degradation returns 0.75."""
    assert compute_eta_scale("controlled_degradation", 0.0) == 0.75
    assert compute_eta_scale("controlled_degradation", 500.0) == 0.75


def test_compute_eta_scale_emergency_stabilization():
    """Test emergency_stabilization returns 0.50."""
    assert compute_eta_scale("emergency_stabilization", 0.0) == 0.50
    assert compute_eta_scale("emergency_stabilization", 100.0) == 0.50


def test_compute_eta_scale_recovery():
    """Test recovery returns 0.25."""
    assert compute_eta_scale("recovery", 0.0) == 0.25
    assert compute_eta_scale("recovery", 1000.0) == 0.25


def test_compute_eta_scale_unknown_regime():
    """Test unknown regime defaults to 1.0 (no scaling)."""
    assert compute_eta_scale("unknown", 100.0) == 1.0
    assert compute_eta_scale("invalid_regime", 500.0) == 1.0
    assert compute_eta_scale("", 100.0) == 1.0


def test_compute_eta_scale_case_insensitive():
    """Test regime names are case-insensitive."""
    assert compute_eta_scale("NORMAL", 100.0) == 1.0
    assert compute_eta_scale("Normal", 100.0) == 1.0
    assert compute_eta_scale("NoRmAl", 100.0) == 1.0


def test_compute_eta_scale_whitespace_trimmed():
    """Test regime names are trimmed of whitespace."""
    assert compute_eta_scale(" normal ", 100.0) == 1.0
    assert compute_eta_scale("  heightened  ", 100.0) == 0.95


# ---------- apply_eta_scaling Tests ----------


def test_apply_eta_scaling_normal_no_change():
    """Test normal regime preserves base η."""
    assert apply_eta_scaling(0.8, "normal", 100.0) == 0.8
    assert apply_eta_scaling(1.0, "normal", 500.0) == 1.0
    assert apply_eta_scaling(0.5, "normal", 1000.0) == 0.5


def test_apply_eta_scaling_heightened_short():
    """Test heightened <5min scales by 0.95."""
    # 0.8 * 0.95 = 0.76
    assert apply_eta_scaling(0.8, "heightened", 100.0) == pytest.approx(0.76)
    # 1.0 * 0.95 = 0.95
    assert apply_eta_scaling(1.0, "heightened", 200.0) == pytest.approx(0.95)


def test_apply_eta_scaling_heightened_long():
    """Test heightened ≥5min scales by 0.90."""
    # 0.8 * 0.90 = 0.72
    assert apply_eta_scaling(0.8, "heightened", 300.0) == pytest.approx(0.72)
    # 1.0 * 0.90 = 0.90
    assert apply_eta_scaling(1.0, "heightened", 500.0) == pytest.approx(0.90)


def test_apply_eta_scaling_emergency():
    """Test emergency_stabilization scales by 0.50."""
    # 0.8 * 0.50 = 0.4
    assert apply_eta_scaling(0.8, "emergency_stabilization", 100.0) == pytest.approx(0.4)
    # 1.0 * 0.50 = 0.50
    assert apply_eta_scaling(1.0, "emergency_stabilization", 200.0) == pytest.approx(0.50)


def test_apply_eta_scaling_recovery():
    """Test recovery scales by 0.25."""
    # 0.8 * 0.25 = 0.2
    assert apply_eta_scaling(0.8, "recovery", 100.0) == pytest.approx(0.2)
    # 1.0 * 0.25 = 0.25
    assert apply_eta_scaling(1.0, "recovery", 500.0) == pytest.approx(0.25)


def test_apply_eta_scaling_freeze_supersedes_all():
    """Test freeze=True overrides to 0.0 regardless of regime."""
    assert apply_eta_scaling(0.8, "normal", 100.0, freeze=True) == 0.0
    assert apply_eta_scaling(1.0, "heightened", 300.0, freeze=True) == 0.0
    assert apply_eta_scaling(0.5, "emergency_stabilization", 50.0, freeze=True) == 0.0


def test_apply_eta_scaling_clamps_to_1_0():
    """Test result never exceeds 1.0 even with base > 1.0."""
    # 1.2 * 1.0 = 1.2, clamped to 1.0
    assert apply_eta_scaling(1.2, "normal", 100.0) == 1.0
    # 1.5 * 0.95 = 1.425, clamped to 1.0
    assert apply_eta_scaling(1.5, "heightened", 100.0) == 1.0


def test_apply_eta_scaling_clamps_to_0_0():
    """Test result never goes below 0.0."""
    # Negative base clamped to 0.0
    assert apply_eta_scaling(-0.5, "normal", 100.0) == 0.0


def test_apply_eta_scaling_multiplicative_not_additive():
    """Test scaling is multiplicative (eta_base * scale_factor)."""
    # 0.6 * 0.90 = 0.54 (not 0.6 + 0.90)
    result = apply_eta_scaling(0.6, "heightened", 300.0)
    assert result == pytest.approx(0.54)
    assert result != pytest.approx(1.5)  # Would be additive


# ---------- get_eta_scaling_metadata Tests ----------


def test_get_eta_scaling_metadata_structure():
    """Test metadata has expected structure."""
    metadata = get_eta_scaling_metadata("heightened", 100.0)

    assert "regime" in metadata
    assert "duration_s" in metadata
    assert "scale_factor" in metadata
    assert "threshold_matched_s" in metadata


def test_get_eta_scaling_metadata_normal():
    """Test metadata for normal regime."""
    metadata = get_eta_scaling_metadata("normal", 500.0)

    assert metadata["regime"] == "normal"
    assert metadata["duration_s"] == 500.0
    assert metadata["scale_factor"] == 1.0
    assert metadata["threshold_matched_s"] == 0.0


def test_get_eta_scaling_metadata_heightened_short():
    """Test metadata for heightened <5min."""
    metadata = get_eta_scaling_metadata("heightened", 100.0)

    assert metadata["regime"] == "heightened"
    assert metadata["duration_s"] == 100.0
    assert metadata["scale_factor"] == 0.95
    assert metadata["threshold_matched_s"] == 0.0  # Matched 0.0 threshold


def test_get_eta_scaling_metadata_heightened_long():
    """Test metadata for heightened ≥5min."""
    metadata = get_eta_scaling_metadata("heightened", 400.0)

    assert metadata["regime"] == "heightened"
    assert metadata["duration_s"] == 400.0
    assert metadata["scale_factor"] == 0.90
    assert metadata["threshold_matched_s"] == 300.0  # Matched 300s threshold


def test_get_eta_scaling_metadata_emergency():
    """Test metadata for emergency_stabilization."""
    metadata = get_eta_scaling_metadata("emergency_stabilization", 50.0)

    assert metadata["regime"] == "emergency_stabilization"
    assert metadata["scale_factor"] == 0.50
    assert metadata["threshold_matched_s"] == 0.0


# ---------- Edge Cases ----------


def test_eta_scaling_zero_duration():
    """Test duration=0.0 uses first threshold."""
    assert compute_eta_scale("heightened", 0.0) == 0.95
    assert compute_eta_scale("emergency_stabilization", 0.0) == 0.50


def test_eta_scaling_very_long_duration():
    """Test very long durations use correct threshold."""
    # Heightened stays at 0.90 even after hours
    assert compute_eta_scale("heightened", 10000.0) == 0.90
    assert compute_eta_scale("heightened", 86400.0) == 0.90  # 24 hours


def test_eta_scaling_exact_threshold_boundary():
    """Test exact threshold boundary (300s) for heightened."""
    # 299.9s should be <5min (0.95)
    assert compute_eta_scale("heightened", 299.9) == 0.95
    # 300.0s should be ≥5min (0.90)
    assert compute_eta_scale("heightened", 300.0) == 0.90
    # 300.1s should be ≥5min (0.90)
    assert compute_eta_scale("heightened", 300.1) == 0.90


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
