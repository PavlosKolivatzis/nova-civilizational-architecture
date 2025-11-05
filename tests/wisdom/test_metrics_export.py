"""Test Prometheus metrics export for wisdom system."""

import pytest

from nova.metrics import wisdom_metrics


def setup_function():
    """Reset metrics before each test."""
    wisdom_metrics.reset_for_tests()


def test_all_gauges_exist():
    """Verify all required gauges are registered."""
    assert wisdom_metrics.wisdom_eta_gauge() is not None
    assert wisdom_metrics.wisdom_gamma_gauge() is not None
    assert wisdom_metrics.wisdom_generativity_gauge() is not None
    assert wisdom_metrics.wisdom_stability_margin_gauge() is not None
    assert wisdom_metrics.wisdom_hopf_distance_gauge() is not None
    assert wisdom_metrics.wisdom_spectral_radius_gauge() is not None


def test_publish_telemetry_updates_gauges():
    """Test that publish_wisdom_telemetry updates all gauges."""
    wisdom_metrics.publish_wisdom_telemetry(
        eta=0.12,
        gamma=0.68,
        generativity=0.75,
        stability_margin=0.08,
        hopf_distance=0.05,
        spectral_radius=0.25,
    )

    assert wisdom_metrics.wisdom_eta_gauge()._value.get() == pytest.approx(0.12)
    assert wisdom_metrics.wisdom_gamma_gauge()._value.get() == pytest.approx(0.68)
    assert wisdom_metrics.wisdom_generativity_gauge()._value.get() == pytest.approx(0.75)
    assert wisdom_metrics.wisdom_stability_margin_gauge()._value.get() == pytest.approx(0.08)
    assert wisdom_metrics.wisdom_hopf_distance_gauge()._value.get() == pytest.approx(0.05)
    assert wisdom_metrics.wisdom_spectral_radius_gauge()._value.get() == pytest.approx(0.25)


def test_reset_clears_all_gauges():
    """Test that reset_for_tests clears all gauges to zero."""
    # Set some values
    wisdom_metrics.publish_wisdom_telemetry(
        eta=0.15,
        gamma=0.80,
        generativity=0.90,
        stability_margin=0.10,
        hopf_distance=0.08,
        spectral_radius=0.30,
    )

    # Reset
    wisdom_metrics.reset_for_tests()

    # All should be zero
    assert wisdom_metrics.wisdom_eta_gauge()._value.get() == pytest.approx(0.0)
    assert wisdom_metrics.wisdom_gamma_gauge()._value.get() == pytest.approx(0.0)
    assert wisdom_metrics.wisdom_generativity_gauge()._value.get() == pytest.approx(0.0)
    assert wisdom_metrics.wisdom_stability_margin_gauge()._value.get() == pytest.approx(0.0)
    assert wisdom_metrics.wisdom_hopf_distance_gauge()._value.get() == pytest.approx(0.0)
    assert wisdom_metrics.wisdom_spectral_radius_gauge()._value.get() == pytest.approx(0.0)


def test_gauge_names():
    """Test that gauges have correct metric names."""
    assert wisdom_metrics.wisdom_eta_gauge()._name == "nova_wisdom_eta_current"
    assert wisdom_metrics.wisdom_gamma_gauge()._name == "nova_wisdom_gamma"
    assert wisdom_metrics.wisdom_generativity_gauge()._name == "nova_wisdom_generativity"
    assert (
        wisdom_metrics.wisdom_stability_margin_gauge()._name
        == "nova_wisdom_stability_margin"
    )
    assert wisdom_metrics.wisdom_hopf_distance_gauge()._name == "nova_wisdom_hopf_distance"
    assert (
        wisdom_metrics.wisdom_spectral_radius_gauge()._name == "nova_wisdom_spectral_radius"
    )


def test_multiple_updates_preserve_latest():
    """Test that multiple updates preserve only the latest value."""
    wisdom_metrics.publish_wisdom_telemetry(
        eta=0.10,
        gamma=0.60,
        generativity=0.50,
        stability_margin=0.05,
        hopf_distance=0.10,
        spectral_radius=0.20,
    )

    wisdom_metrics.publish_wisdom_telemetry(
        eta=0.15,
        gamma=0.70,
        generativity=0.80,
        stability_margin=0.10,
        hopf_distance=0.03,
        spectral_radius=0.35,
    )

    # Should have latest values
    assert wisdom_metrics.wisdom_eta_gauge()._value.get() == pytest.approx(0.15)
    assert wisdom_metrics.wisdom_gamma_gauge()._value.get() == pytest.approx(0.70)
    assert wisdom_metrics.wisdom_generativity_gauge()._value.get() == pytest.approx(0.80)
