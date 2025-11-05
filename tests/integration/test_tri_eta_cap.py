"""
Integration test: TRI coherence → wisdom governor eta cap feedback.

Verifies that:
1. High coherence (stable TRI) allows higher η
2. Low coherence (unstable TRI) caps η lower
3. Feedback loop correctly limits governor output
"""

import os

import pytest

from nova.slots.slot04_tri.wisdom_feedback import compute_tri_eta_cap


def setup_function():
    """Reset TRI feedback config."""
    for key in ["NOVA_TRI_COHERENCE_HIGH", "NOVA_TRI_COHERENCE_LOW",
                "NOVA_TRI_ETA_CAP_HIGH", "NOVA_TRI_ETA_CAP_LOW"]:
        os.environ.pop(key, None)


def test_low_coherence_caps_eta_low():
    """Test that unstable TRI (low C) caps η low."""
    # C = 0.30 (unstable) → η_cap = 0.08
    eta_cap = compute_tri_eta_cap(coherence=0.30)
    assert eta_cap == pytest.approx(0.08)


def test_high_coherence_allows_high_eta():
    """Test that stable TRI (high C) allows high η."""
    # C = 0.90 (very stable) → η_cap = 0.18
    eta_cap = compute_tri_eta_cap(coherence=0.90)
    assert eta_cap == pytest.approx(0.18)


def test_mid_coherence_interpolates():
    """Test that mid-range coherence uses linear interpolation."""
    # C = 0.625 (midpoint) → interpolated η_cap
    eta_cap = compute_tri_eta_cap(coherence=0.625)

    # Expected: 0.08 + (0.625 - 0.40) / (0.85 - 0.40) * (0.18 - 0.08)
    expected = 0.08 + (0.625 - 0.40) / (0.85 - 0.40) * (0.18 - 0.08)
    assert eta_cap == pytest.approx(expected)


def test_coherence_range_mapping():
    """Test full range of coherence → eta_cap mapping."""
    # Very low coherence
    assert compute_tri_eta_cap(0.0) == pytest.approx(0.08)

    # Low threshold
    assert compute_tri_eta_cap(0.40) == pytest.approx(0.08)

    # Mid-range
    mid_cap = compute_tri_eta_cap(0.625)
    assert 0.08 < mid_cap < 0.18

    # High threshold
    assert compute_tri_eta_cap(0.85) == pytest.approx(0.18)

    # Very high coherence
    assert compute_tri_eta_cap(1.0) == pytest.approx(0.18)


def test_monotonic_increase():
    """Test that eta_cap increases monotonically with coherence."""
    coherences = [0.0, 0.2, 0.4, 0.6, 0.8, 1.0]
    eta_caps = [compute_tri_eta_cap(c) for c in coherences]

    # Each eta_cap should be >= previous
    for i in range(1, len(eta_caps)):
        assert eta_caps[i] >= eta_caps[i - 1]


def test_custom_config_coherence_mapping():
    """Test that custom config is respected in mapping."""
    os.environ["NOVA_TRI_COHERENCE_HIGH"] = "0.80"
    os.environ["NOVA_TRI_COHERENCE_LOW"] = "0.50"
    os.environ["NOVA_TRI_ETA_CAP_HIGH"] = "0.15"
    os.environ["NOVA_TRI_ETA_CAP_LOW"] = "0.10"

    # Below low threshold
    assert compute_tri_eta_cap(0.40) == pytest.approx(0.10)

    # At midpoint
    assert compute_tri_eta_cap(0.65) == pytest.approx(0.125)

    # Above high threshold
    assert compute_tri_eta_cap(0.90) == pytest.approx(0.15)


def test_feedback_loop_limits_governor():
    """Test that TRI cap effectively limits governor output."""
    # Simulate governor wanting η = 0.15
    governor_eta = 0.15

    # Low coherence caps it to 0.08
    tri_cap = compute_tri_eta_cap(coherence=0.30)
    effective_eta = min(governor_eta, tri_cap)

    assert effective_eta == pytest.approx(0.08)  # Capped


def test_feedback_loop_allows_governor_when_stable():
    """Test that high coherence allows governor freedom."""
    # Simulate governor wanting η = 0.15
    governor_eta = 0.15

    # High coherence allows up to 0.18, so no capping
    tri_cap = compute_tri_eta_cap(coherence=0.90)
    effective_eta = min(governor_eta, tri_cap)

    assert effective_eta == pytest.approx(0.15)  # Not capped


def test_coherence_boundary_behavior():
    """Test exact boundary coherence values."""
    # At low boundary
    cap_low = compute_tri_eta_cap(0.40)
    assert cap_low == pytest.approx(0.08)

    # Just above low boundary
    cap_above_low = compute_tri_eta_cap(0.41)
    assert cap_above_low > 0.08

    # Just below high boundary
    cap_below_high = compute_tri_eta_cap(0.84)
    assert cap_below_high < 0.18

    # At high boundary
    cap_high = compute_tri_eta_cap(0.85)
    assert cap_high == pytest.approx(0.18)


def test_coherence_stability_safety():
    """Test that low coherence enforces safety."""
    # Very unstable token distribution
    unstable_coherence = 0.20

    eta_cap = compute_tri_eta_cap(unstable_coherence)

    # Should enforce conservative cap
    assert eta_cap == pytest.approx(0.08)
    assert eta_cap < 0.12  # Significantly below typical operating range
