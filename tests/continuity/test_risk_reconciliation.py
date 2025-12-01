"""
Test Unified Risk Field (URF) reconciliation calculator.

Phase 9 integration - verify compute_risk_alignment() and record_urf().
"""

import pytest
from src.nova.continuity.risk_reconciliation import (
    compute_risk_alignment,
    get_unified_risk_field,
    _clamp
)
from nova.orchestrator.prometheus_metrics import record_urf


def test_compute_risk_alignment_perfect():
    """Test perfect alignment - both signals agree."""
    result = compute_risk_alignment(rri=0.85, collapse_risk=0.85)

    assert result["rri"] == 0.85
    assert result["predictive_collapse_risk"] == 0.85
    assert result["risk_gap"] == 0.0
    assert result["alignment_score"] == 1.0
    assert result["composite_risk"] == pytest.approx(0.85, abs=0.01)
    assert result["weights"] == {"rri": 0.4, "collapse_risk": 0.6}
    assert "timestamp" in result


def test_compute_risk_alignment_divergent():
    """Test divergent signals - large gap between RRI and collapse_risk."""
    result = compute_risk_alignment(rri=0.3, collapse_risk=0.8)

    assert result["rri"] == 0.3
    assert result["predictive_collapse_risk"] == 0.8
    assert result["risk_gap"] == 0.5
    assert result["alignment_score"] == 0.5

    # Weighted mean: 0.4*0.3 + 0.6*0.8 = 0.12 + 0.48 = 0.6
    assert result["composite_risk"] == pytest.approx(0.6, abs=0.01)


def test_compute_risk_alignment_convergent_high_risk():
    """Test convergent high risk - both signals elevated."""
    result = compute_risk_alignment(rri=0.2, collapse_risk=0.15)

    assert result["rri"] == 0.2
    assert result["predictive_collapse_risk"] == 0.15
    assert result["risk_gap"] == pytest.approx(0.05, abs=0.01)
    assert result["alignment_score"] == pytest.approx(0.95, abs=0.01)

    # Weighted mean: 0.4*0.2 + 0.6*0.15 = 0.08 + 0.09 = 0.17
    assert result["composite_risk"] == pytest.approx(0.17, abs=0.01)


def test_risk_gap_clamping():
    """Test that out-of-range inputs are clamped to [0.0, 1.0]."""
    result = compute_risk_alignment(rri=-0.5, collapse_risk=1.5)

    assert result["rri"] == 0.0  # Clamped from -0.5
    assert result["predictive_collapse_risk"] == 1.0  # Clamped from 1.5
    assert result["risk_gap"] == 1.0
    assert result["alignment_score"] == 0.0
    assert 0.0 <= result["composite_risk"] <= 1.0


def test_composite_risk_weighting():
    """Test custom weight configuration."""
    result = compute_risk_alignment(
        rri=0.4,
        collapse_risk=0.6,
        weights={"rri": 0.5, "collapse_risk": 0.5}  # Equal weighting
    )

    # Equal weights: 0.5*0.4 + 0.5*0.6 = 0.2 + 0.3 = 0.5
    assert result["composite_risk"] == pytest.approx(0.5, abs=0.01)
    assert result["weights"] == {"rri": 0.5, "collapse_risk": 0.5}


def test_get_unified_risk_field_integration():
    """Test end-to-end gauge reads (fallback if gauges not initialized)."""
    result = get_unified_risk_field()

    # Should return valid structure even if gauges not available
    assert "rri" in result
    assert "predictive_collapse_risk" in result
    assert "risk_gap" in result
    assert "alignment_score" in result
    assert "composite_risk" in result
    assert "weights" in result
    assert "timestamp" in result

    # All values should be in [0.0, 1.0]
    assert 0.0 <= result["rri"] <= 1.0
    assert 0.0 <= result["predictive_collapse_risk"] <= 1.0
    assert 0.0 <= result["risk_gap"] <= 1.0
    assert 0.0 <= result["alignment_score"] <= 1.0
    assert 0.0 <= result["composite_risk"] <= 1.0


def test_record_urf_basic():
    """Test basic URF metric recording."""
    urf = {
        "alignment_score": 0.85,
        "risk_gap": 0.15,
        "composite_risk": 0.6
    }

    # Should not raise
    record_urf(urf)


def test_record_urf_boundary_values():
    """Test URF recording with boundary values."""
    urf = {
        "alignment_score": 0.0,
        "risk_gap": 1.0,
        "composite_risk": 0.0
    }
    record_urf(urf)

    urf = {
        "alignment_score": 1.0,
        "risk_gap": 0.0,
        "composite_risk": 1.0
    }
    record_urf(urf)


def test_record_urf_missing_keys():
    """Test URF recording with missing keys defaults gracefully."""
    urf = {}

    # Should not raise, defaults to safe values
    record_urf(urf)


def test_clamp_helper():
    """Test internal clamping helper."""
    assert _clamp(-0.5) == 0.0
    assert _clamp(1.5) == 1.0
    assert _clamp(0.5) == 0.5
    assert _clamp(0.0) == 0.0
    assert _clamp(1.0) == 1.0
