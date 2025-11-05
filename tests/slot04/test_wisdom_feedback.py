"""Test TRI wisdom feedback module."""

import os

import pytest

from nova.slots.slot04_tri import wisdom_feedback as module


def setup_function():
    """Clear environment before each test."""
    for key in ["NOVA_TRI_COHERENCE_HIGH", "NOVA_TRI_COHERENCE_LOW",
                "NOVA_TRI_ETA_CAP_HIGH", "NOVA_TRI_ETA_CAP_LOW"]:
        os.environ.pop(key, None)


def test_high_coherence_gives_high_cap():
    """Test that very stable systems (high C) get high eta cap."""
    # C > 0.85 → η_cap = 0.18
    eta_cap = module.compute_tri_eta_cap(coherence=0.90)
    assert eta_cap == pytest.approx(0.18)


def test_low_coherence_gives_low_cap():
    """Test that unstable systems (low C) get low eta cap."""
    # C < 0.40 → η_cap = 0.08
    eta_cap = module.compute_tri_eta_cap(coherence=0.30)
    assert eta_cap == pytest.approx(0.08)


def test_mid_coherence_linear_interpolation():
    """Test linear interpolation in mid-range coherence."""
    # C = 0.625 (midpoint between 0.40 and 0.85)
    # Should give midpoint between 0.08 and 0.18 = 0.13
    eta_cap = module.compute_tri_eta_cap(coherence=0.625)
    expected = 0.08 + (0.18 - 0.08) * (0.625 - 0.40) / (0.85 - 0.40)
    assert eta_cap == pytest.approx(expected)


def test_coherence_clamping():
    """Test that coherence values outside [0,1] are clamped."""
    # C > 1.0 should be treated as 1.0 → high cap
    eta_cap_high = module.compute_tri_eta_cap(coherence=1.5)
    assert eta_cap_high == pytest.approx(0.18)

    # C < 0.0 should be treated as 0.0 → low cap
    eta_cap_low = module.compute_tri_eta_cap(coherence=-0.5)
    assert eta_cap_low == pytest.approx(0.08)


def test_config_from_environment():
    """Test reading configuration from environment."""
    os.environ["NOVA_TRI_COHERENCE_HIGH"] = "0.90"
    os.environ["NOVA_TRI_COHERENCE_LOW"] = "0.35"
    os.environ["NOVA_TRI_ETA_CAP_HIGH"] = "0.20"
    os.environ["NOVA_TRI_ETA_CAP_LOW"] = "0.05"

    high_thresh, low_thresh, eta_high, eta_low = module.get_feedback_config()

    assert high_thresh == pytest.approx(0.90)
    assert low_thresh == pytest.approx(0.35)
    assert eta_high == pytest.approx(0.20)
    assert eta_low == pytest.approx(0.05)


def test_config_safety_ordering():
    """Test that config enforces threshold ordering."""
    os.environ["NOVA_TRI_COHERENCE_HIGH"] = "0.40"
    os.environ["NOVA_TRI_COHERENCE_LOW"] = "0.50"  # Invalid: low > high

    high_thresh, low_thresh, eta_high, eta_low = module.get_feedback_config()

    # Should be corrected
    assert low_thresh < high_thresh


def test_custom_config_interpolation():
    """Test that custom config is used for interpolation."""
    os.environ["NOVA_TRI_COHERENCE_HIGH"] = "0.80"
    os.environ["NOVA_TRI_COHERENCE_LOW"] = "0.50"
    os.environ["NOVA_TRI_ETA_CAP_HIGH"] = "0.15"
    os.environ["NOVA_TRI_ETA_CAP_LOW"] = "0.10"

    # C = 0.65 (midpoint between 0.50 and 0.80)
    # Should give midpoint between 0.10 and 0.15 = 0.125
    eta_cap = module.compute_tri_eta_cap(coherence=0.65)
    assert eta_cap == pytest.approx(0.125)


def test_get_tri_coherence_returns_none_when_unavailable():
    """Test that get_tri_coherence gracefully returns None when unavailable."""
    # Semantic mirror not available in test environment
    coherence = module.get_tri_coherence()
    # Should return None without raising
    assert coherence is None


def test_feedback_status():
    """Test get_feedback_status for monitoring."""
    status = module.get_feedback_status()

    assert "coherence" in status
    assert "eta_cap" in status
    assert "available" in status
    assert "config" in status
    assert isinstance(status["config"], dict)


def test_boundary_values():
    """Test exact boundary values for thresholds."""
    # Exactly at high threshold
    eta_cap_high = module.compute_tri_eta_cap(coherence=0.85)
    assert eta_cap_high == pytest.approx(0.18)

    # Exactly at low threshold
    eta_cap_low = module.compute_tri_eta_cap(coherence=0.40)
    assert eta_cap_low == pytest.approx(0.08)


def test_public_api():
    """Test that only intended symbols are exported."""
    public = {name for name in dir(module) if not name.startswith("_")}
    expected = {
        "compute_tri_eta_cap",
        "get_tri_coherence",
        "get_feedback_config",
        "get_feedback_status",
        "__all__",
        "os",
        "Optional",
    }
    assert public <= expected

    exported = set(module.__all__)
    assert exported == {"compute_tri_eta_cap", "get_tri_coherence", "get_feedback_config"}
