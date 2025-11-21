"""
Unit tests for Resonance Integrity Score (RIS) Calculator — Phase 7.0-RC

Tests RIS computation formula: RIS = sqrt(M_s × E_c)
Where M_s = Memory Stability, E_c = Ethical Compliance
"""
import pytest
import math
from orchestrator.predictive.ris_calculator import (
    compute_ris,
    compute_ris_with_smoothing,
    ris_to_dict,
    _resolve_ethical_compliance,
)


class TestComputeRIS:
    """Test core RIS computation logic."""

    def test_ris_formula_perfect_inputs(self):
        """Perfect inputs (1.0 × 1.0) should yield RIS = 1.0."""
        ris = compute_ris(memory_stability=1.0, ethical_compliance=1.0)
        assert ris == pytest.approx(1.0, abs=0.001)

    def test_ris_formula_half_inputs(self):
        """Half inputs (0.5 × 0.5) should yield RIS = sqrt(0.25) = 0.5."""
        ris = compute_ris(memory_stability=0.5, ethical_compliance=0.5)
        assert ris == pytest.approx(0.5, abs=0.001)

    def test_ris_formula_zero_memory_stability(self):
        """Zero memory stability should yield RIS = 0.0 regardless of ethics."""
        ris = compute_ris(memory_stability=0.0, ethical_compliance=1.0)
        assert ris == pytest.approx(0.0, abs=0.001)

    def test_ris_formula_zero_ethical_compliance(self):
        """Zero ethical compliance should yield RIS = 0.0 regardless of memory."""
        ris = compute_ris(memory_stability=1.0, ethical_compliance=0.0)
        assert ris == pytest.approx(0.0, abs=0.001)

    def test_ris_formula_asymmetric_inputs(self):
        """Asymmetric inputs should follow sqrt(M_s × E_c) formula."""
        # High memory, low ethics
        ris1 = compute_ris(memory_stability=0.9, ethical_compliance=0.4)
        expected1 = math.sqrt(0.9 * 0.4)
        assert ris1 == pytest.approx(expected1, abs=0.001)

        # Low memory, high ethics
        ris2 = compute_ris(memory_stability=0.4, ethical_compliance=0.9)
        expected2 = math.sqrt(0.4 * 0.9)
        assert ris2 == pytest.approx(expected2, abs=0.001)

    def test_ris_clamping_above_one(self):
        """RIS should clamp values above 1.0 (defensive)."""
        # Should not happen with valid inputs, but test defensively
        ris = compute_ris(memory_stability=1.5, ethical_compliance=1.5)
        assert ris <= 1.0

    def test_ris_clamping_below_zero(self):
        """RIS should clamp values below 0.0 (defensive)."""
        ris = compute_ris(memory_stability=-0.5, ethical_compliance=-0.5)
        assert ris >= 0.0

    def test_ris_typical_operational_values(self):
        """Test typical operational values during normal operation."""
        # Typical stable state: high memory, high ethics
        ris = compute_ris(memory_stability=0.85, ethical_compliance=0.90)
        expected = math.sqrt(0.85 * 0.90)
        assert ris == pytest.approx(expected, abs=0.001)
        assert 0.85 <= ris <= 0.90

    def test_ris_degraded_state(self):
        """Test degraded state with lower stability."""
        # Degraded: memory dropping, ethics holding
        ris = compute_ris(memory_stability=0.65, ethical_compliance=0.85)
        expected = math.sqrt(0.65 * 0.85)
        assert ris == pytest.approx(expected, abs=0.001)
        assert ris < 0.80  # Below RC threshold


class TestEthicalComplianceResolution:
    """Test ethical compliance resolution hierarchy."""

    def test_explicit_value_overrides_hierarchy(self):
        """Explicit value should take precedence over all fallbacks."""
        ec = _resolve_ethical_compliance(explicit_value=0.75)
        assert ec == pytest.approx(0.75, abs=0.001)

    def test_explicit_value_clamped_above_one(self):
        """Explicit value above 1.0 should be clamped."""
        ec = _resolve_ethical_compliance(explicit_value=1.5)
        assert ec == 1.0

    def test_explicit_value_clamped_below_zero(self):
        """Explicit value below 0.0 should be clamped."""
        ec = _resolve_ethical_compliance(explicit_value=-0.5)
        assert ec == 0.0

    def test_local_mode_fallback(self):
        """With no explicit value and no mirror, should return 1.0 (local mode)."""
        # No semantic mirror available in test environment
        ec = _resolve_ethical_compliance(explicit_value=None)
        assert ec == 1.0  # Local mode: neutral trust


class TestRISWithSmoothing:
    """Test RIS computation with exponential smoothing."""

    def test_smoothing_no_previous_ris(self):
        """With no previous RIS, should return current RIS unsmoothed."""
        ris = compute_ris_with_smoothing(
            memory_stability=0.8,
            ethical_compliance=0.9,
            previous_ris=None
        )
        expected = math.sqrt(0.8 * 0.9)
        assert ris == pytest.approx(expected, abs=0.001)

    def test_smoothing_alpha_one(self):
        """Alpha=1.0 should return current RIS (no smoothing)."""
        current_ris = math.sqrt(0.8 * 0.9)
        ris = compute_ris_with_smoothing(
            memory_stability=0.8,
            ethical_compliance=0.9,
            previous_ris=0.5,
            alpha=1.0
        )
        assert ris == pytest.approx(current_ris, abs=0.001)

    def test_smoothing_alpha_zero(self):
        """Alpha=0.0 should return previous RIS (no update)."""
        ris = compute_ris_with_smoothing(
            memory_stability=0.8,
            ethical_compliance=0.9,
            previous_ris=0.5,
            alpha=0.0
        )
        assert ris == pytest.approx(0.5, abs=0.001)

    def test_smoothing_alpha_half(self):
        """Alpha=0.5 should average current and previous RIS."""
        current_ris = math.sqrt(0.8 * 0.9)  # ≈ 0.849
        previous_ris = 0.7
        ris = compute_ris_with_smoothing(
            memory_stability=0.8,
            ethical_compliance=0.9,
            previous_ris=previous_ris,
            alpha=0.5
        )
        expected = (0.5 * current_ris) + (0.5 * previous_ris)
        assert ris == pytest.approx(expected, abs=0.001)

    def test_smoothing_reduces_volatility(self):
        """Smoothing should reduce step changes in RIS."""
        # Start at high RIS
        previous_ris = 0.9

        # Drop to low RIS
        current_ris = math.sqrt(0.5 * 0.5)  # = 0.5

        # Smoothed should be between previous and current
        smoothed = compute_ris_with_smoothing(
            memory_stability=0.5,
            ethical_compliance=0.5,
            previous_ris=previous_ris,
            alpha=0.5
        )

        assert current_ris < smoothed < previous_ris

    def test_smoothing_clamping(self):
        """Smoothed RIS should still be clamped to [0.0, 1.0]."""
        # Edge case: should not exceed bounds even with smoothing
        ris = compute_ris_with_smoothing(
            memory_stability=1.0,
            ethical_compliance=1.0,
            previous_ris=1.0,
            alpha=0.5
        )
        assert 0.0 <= ris <= 1.0


class TestRISToDict:
    """Test RIS serialization for semantic mirror publishing."""

    def test_ris_to_dict_structure(self):
        """Should serialize RIS with all required fields."""
        snapshot = ris_to_dict(
            ris=0.85,
            memory_stability=0.90,
            ethical_compliance=0.95,
            timestamp=1234567890.0
        )

        assert "ris" in snapshot
        assert "memory_stability" in snapshot
        assert "ethical_compliance" in snapshot
        assert "timestamp" in snapshot
        assert "version" in snapshot

    def test_ris_to_dict_values(self):
        """Should preserve exact values."""
        snapshot = ris_to_dict(
            ris=0.85,
            memory_stability=0.90,
            ethical_compliance=0.95,
            timestamp=1234567890.0
        )

        assert snapshot["ris"] == 0.85
        assert snapshot["memory_stability"] == 0.90
        assert snapshot["ethical_compliance"] == 0.95
        assert snapshot["timestamp"] == 1234567890.0
        assert snapshot["version"] == "7.0-RC"

    def test_ris_to_dict_version_tracking(self):
        """Should include version for RC attestation."""
        snapshot = ris_to_dict(
            ris=0.85,
            memory_stability=0.90,
            ethical_compliance=0.95,
            timestamp=1234567890.0
        )

        assert "version" in snapshot
        assert "7.0" in snapshot["version"]


class TestRISIntegration:
    """Integration tests for RIS computation."""

    def test_ris_rc_success_threshold(self):
        """RIS ≥ 0.75 should indicate RC success."""
        # High memory + high ethics → RIS ≥ 0.75
        ris = compute_ris(memory_stability=0.85, ethical_compliance=0.85)
        assert ris >= 0.75  # RC success threshold

    def test_ris_rc_failure_threshold(self):
        """RIS < 0.75 should indicate RC failure."""
        # Low memory or low ethics → RIS < 0.75
        ris = compute_ris(memory_stability=0.60, ethical_compliance=0.80)
        assert ris < 0.75  # Below RC threshold

    def test_ris_memory_sensitivity(self):
        """RIS should be sensitive to memory stability changes."""
        ris_high_memory = compute_ris(memory_stability=0.9, ethical_compliance=0.8)
        ris_low_memory = compute_ris(memory_stability=0.5, ethical_compliance=0.8)

        # Should see significant difference
        assert ris_high_memory > ris_low_memory
        assert (ris_high_memory - ris_low_memory) > 0.2

    def test_ris_ethical_sensitivity(self):
        """RIS should be sensitive to ethical compliance changes."""
        ris_high_ethics = compute_ris(memory_stability=0.8, ethical_compliance=0.9)
        ris_low_ethics = compute_ris(memory_stability=0.8, ethical_compliance=0.5)

        # Should see significant difference
        assert ris_high_ethics > ris_low_ethics
        assert (ris_high_ethics - ris_low_ethics) > 0.2

    def test_ris_symmetry(self):
        """RIS should be symmetric in M_s and E_c."""
        ris1 = compute_ris(memory_stability=0.6, ethical_compliance=0.9)
        ris2 = compute_ris(memory_stability=0.9, ethical_compliance=0.6)

        # Should be identical (commutative)
        assert ris1 == pytest.approx(ris2, abs=0.001)
