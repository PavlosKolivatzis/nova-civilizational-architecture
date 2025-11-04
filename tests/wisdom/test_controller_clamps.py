"""Test controller clamps and safety protocols."""

import pytest

from nova.governor.adaptive_wisdom import AdaptiveWisdomGovernor


def test_critical_clamp():
    """Test immediate clamp to η_min when S < 0.01."""
    gov = AdaptiveWisdomGovernor(eta=0.12, eta_min=0.05, eta_max=0.18)

    # S < 0.01 should trigger CRITICAL mode
    telemetry = gov.step(margin=0.005, G=0.50)

    assert telemetry.eta == 0.05
    assert telemetry.mode == "CRITICAL"


def test_stabilizing_mode():
    """Test STABILIZING mode for low but non-critical margins."""
    gov = AdaptiveWisdomGovernor(eta=0.12, eta_min=0.05, eta_max=0.18)

    # 0.01 < S < 0.02 should trigger STABILIZING
    telemetry = gov.step(margin=0.015, G=0.60)

    assert telemetry.eta == pytest.approx(0.08)
    assert telemetry.mode == "STABILIZING"


def test_optimal_mode():
    """Test OPTIMAL mode for good stability and generativity."""
    gov = AdaptiveWisdomGovernor(eta=0.10, eta_min=0.05, eta_max=0.18)

    # S > 0.05 and G >= 0.70 should trigger OPTIMAL
    telemetry = gov.step(margin=0.08, G=0.72)

    assert telemetry.eta == pytest.approx(0.12)
    assert telemetry.mode == "OPTIMAL"


def test_exploring_mode():
    """Test EXPLORING mode when stable but underperforming."""
    gov = AdaptiveWisdomGovernor(eta=0.10, eta_min=0.05, eta_max=0.18)

    # S > 0.10 and G < 0.60 should trigger EXPLORING
    telemetry = gov.step(margin=0.15, G=0.40)

    # Should increase eta (up to 1.1x, capped at 0.18)
    assert telemetry.eta > 0.10
    assert telemetry.eta <= 0.18
    assert telemetry.mode == "EXPLORING"


def test_safe_mode_default():
    """Test SAFE mode as default fallback."""
    gov = AdaptiveWisdomGovernor(eta=0.10, eta_min=0.05, eta_max=0.18)

    # Moderate conditions should trigger SAFE
    telemetry = gov.step(margin=0.03, G=0.55)

    assert telemetry.eta == pytest.approx(0.08)
    assert telemetry.mode == "SAFE"


def test_eta_bounds_enforced():
    """Test that eta always stays within [eta_min, eta_max]."""
    gov = AdaptiveWisdomGovernor(eta=0.10, eta_min=0.05, eta_max=0.15)

    # Try to trigger high eta
    for _ in range(10):
        telemetry = gov.step(margin=0.20, G=0.20)

    # Should be capped at eta_max
    assert telemetry.eta <= 0.15

    # Try to trigger low eta
    telemetry = gov.step(margin=0.001, G=0.80)

    # Should be at eta_min
    assert telemetry.eta == 0.05


def test_bounds_swap_if_inverted():
    """Test that inverted bounds are corrected."""
    gov = AdaptiveWisdomGovernor(eta=0.10, eta_min=0.20, eta_max=0.05)

    # Should swap: eta_min=0.05, eta_max=0.20
    assert gov.eta_min == 0.05
    assert gov.eta_max == 0.20


def test_telemetry_includes_all_fields():
    """Test that telemetry returns all expected fields."""
    gov = AdaptiveWisdomGovernor()
    telemetry = gov.step(margin=0.08, G=0.70)

    assert hasattr(telemetry, "eta")
    assert hasattr(telemetry, "margin")
    assert hasattr(telemetry, "G")
    assert hasattr(telemetry, "mode")

    assert isinstance(telemetry.eta, float)
    assert isinstance(telemetry.margin, float)
    assert isinstance(telemetry.G, float)
    assert isinstance(telemetry.mode, str)
    assert telemetry.mode in ("CRITICAL", "STABILIZING", "EXPLORING", "OPTIMAL", "SAFE")
