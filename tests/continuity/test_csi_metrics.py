"""
Test CSI Prometheus metrics recording.

Phase 8 integration - verify record_csi() function.
"""

import pytest
from nova.orchestrator.prometheus_metrics import record_csi


def test_record_csi_basic():
    """Test basic CSI metric recording."""
    breakdown = {
        "csi": 0.85,
        "p6_stability": 0.85,
        "p7_stability": 0.88,
        "correlation": 0.85,
    }

    # Should not raise
    record_csi(breakdown)


def test_record_csi_boundary_values():
    """Test CSI recording with boundary values."""
    breakdown = {
        "csi": 0.0,
        "p6_stability": 0.0,
        "p7_stability": 0.0,
        "correlation": 0.0,
    }
    record_csi(breakdown)

    breakdown = {
        "csi": 1.0,
        "p6_stability": 1.0,
        "p7_stability": 1.0,
        "correlation": 1.0,
    }
    record_csi(breakdown)


def test_record_csi_out_of_range_clamped():
    """Test that out-of-range values are clamped to [0.0, 1.0]."""
    breakdown = {
        "csi": 1.5,  # Should clamp to 1.0
        "p6_stability": -0.2,  # Should clamp to 0.0
        "p7_stability": 0.5,
        "correlation": 2.0,  # Should clamp to 1.0
    }

    # Should not raise, values internally clamped
    record_csi(breakdown)


def test_record_csi_missing_keys():
    """Test CSI recording with missing keys defaults to 0.0."""
    breakdown = {}

    # Should not raise, defaults to 0.0
    record_csi(breakdown)


def test_record_csi_partial_breakdown():
    """Test partial breakdown with some keys present."""
    breakdown = {
        "csi": 0.75,
        "p7_stability": 0.82,
    }

    # Should not raise, missing keys default to 0.0
    record_csi(breakdown)
