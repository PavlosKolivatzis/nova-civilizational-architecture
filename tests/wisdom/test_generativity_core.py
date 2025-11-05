"""Test generativity core computation (P, N, Cc, G*, Δη)."""

import pytest

from nova.wisdom.generativity_core import (
    GenerativityParams,
    compute_components,
    compute_gstar,
    eta_bias,
)


def test_components_in_range():
    """Test that all components are in [0,1] range."""
    P, N, Cc = compute_components(
        gamma_avg_1m=0.72,
        gamma_avg_5m=0.68,
        eta_series_1m=[0.10, 0.11, 0.10, 0.09],
        peer_quality_series_1m=[0.8, 0.7, 0.9],
    )

    assert 0 <= P <= 1, f"Progress P={P} out of range"
    assert 0 <= N <= 1, f"Novelty N={N} out of range"
    assert 0 <= Cc <= 1, f"Consistency Cc={Cc} out of range"


def test_gstar_in_range():
    """Test that G* is in [0,1] range."""
    params = GenerativityParams()
    P, N, Cc = compute_components(
        gamma_avg_1m=0.72,
        gamma_avg_5m=0.68,
        eta_series_1m=[0.10, 0.11, 0.10, 0.09],
        peer_quality_series_1m=[0.8, 0.7, 0.9],
    )

    g = compute_gstar(params, P, N, Cc)
    assert 0 <= g <= 1, f"G*={g} out of range"


def test_eta_bias_sign():
    """Test that bias sign matches G* - G₀."""
    params = GenerativityParams(g0=0.6, kappa=0.02)

    # G* > G₀ → positive bias (increase learning)
    bias_high = eta_bias(params, 0.8)
    assert bias_high > 0, "Expected positive bias when G* > G₀"

    # G* < G₀ → negative bias (decrease learning)
    bias_low = eta_bias(params, 0.4)
    assert bias_low < 0, "Expected negative bias when G* < G₀"

    # G* = G₀ → zero bias
    bias_zero = eta_bias(params, 0.6)
    assert abs(bias_zero) < 1e-9, "Expected zero bias when G* = G₀"


def test_progress_component():
    """Test progress P = (γ_1m - γ_5m) / γ_5m."""
    # Positive growth
    P1, _, _ = compute_components(
        gamma_avg_1m=0.72,
        gamma_avg_5m=0.68,
        eta_series_1m=[0.10],
        peer_quality_series_1m=[0.8],
    )
    assert P1 > 0, "Expected positive progress when γ growing"

    # Negative growth (decline)
    P2, _, _ = compute_components(
        gamma_avg_1m=0.65,
        gamma_avg_5m=0.70,
        eta_series_1m=[0.10],
        peer_quality_series_1m=[0.8],
    )
    assert P2 == 0.0, "Expected zero progress (clamped) when γ declining"

    # No change
    P3, _, _ = compute_components(
        gamma_avg_1m=0.70,
        gamma_avg_5m=0.70,
        eta_series_1m=[0.10],
        peer_quality_series_1m=[0.8],
    )
    assert P3 == pytest.approx(0.0), "Expected zero progress when γ stable"


def test_novelty_component():
    """Test novelty N = std(peer_quality) / 0.5."""
    # High spread → high novelty
    _, N1, _ = compute_components(
        gamma_avg_1m=0.70,
        gamma_avg_5m=0.70,
        eta_series_1m=[0.10],
        peer_quality_series_1m=[0.1, 0.9, 0.2, 0.8],  # High variance
    )
    assert N1 > 0.3, "Expected high novelty with diverse peer qualities"

    # Low spread → low novelty
    _, N2, _ = compute_components(
        gamma_avg_1m=0.70,
        gamma_avg_5m=0.70,
        eta_series_1m=[0.10],
        peer_quality_series_1m=[0.7, 0.71, 0.69, 0.70],  # Low variance
    )
    assert N2 < 0.2, "Expected low novelty with similar peer qualities"


def test_consistency_component():
    """Test consistency Cc = 1 - cv(η)."""
    # Low η variability → high consistency
    _, _, Cc1 = compute_components(
        gamma_avg_1m=0.70,
        gamma_avg_5m=0.70,
        eta_series_1m=[0.10, 0.10, 0.10, 0.10],  # Stable η
        peer_quality_series_1m=[0.8],
    )
    assert Cc1 > 0.9, "Expected high consistency with stable η"

    # High η variability → low consistency
    _, _, Cc2 = compute_components(
        gamma_avg_1m=0.70,
        gamma_avg_5m=0.70,
        eta_series_1m=[0.05, 0.15, 0.06, 0.14],  # Volatile η
        peer_quality_series_1m=[0.8],
    )
    assert Cc2 < 0.7, "Expected low consistency with volatile η"


def test_empty_inputs():
    """Test behavior with empty input series."""
    P, N, Cc = compute_components(
        gamma_avg_1m=0.70,
        gamma_avg_5m=0.70,
        eta_series_1m=[],
        peer_quality_series_1m=[],
    )

    # Should handle empty gracefully
    assert 0 <= P <= 1
    assert N == pytest.approx(0.0), "Expected zero novelty with no peers"
    assert Cc == pytest.approx(1.0), "Expected high consistency (no cv) with no η data"


def test_custom_params():
    """Test generativity with custom parameters."""
    params = GenerativityParams(alpha=0.5, beta=0.3, gamma=0.2, g0=0.7, kappa=0.03)

    # Compute with specific components
    P, N, Cc = 0.6, 0.4, 0.8
    g = compute_gstar(params, P, N, Cc)

    # Verify weighted sum
    expected = 0.5 * 0.6 + 0.3 * 0.4 + 0.2 * 0.8
    assert g == pytest.approx(expected, abs=0.01)

    # Verify bias magnitude
    bias = eta_bias(params, g)
    expected_bias = 0.03 * (g - 0.7)
    assert bias == pytest.approx(expected_bias, abs=0.001)


def test_clipping_behavior():
    """Test that components and G* are clipped to [0,1]."""
    # Extreme growth (should be clipped to 1.0)
    P_extreme, _, _ = compute_components(
        gamma_avg_1m=0.99,
        gamma_avg_5m=0.10,  # Huge growth
        eta_series_1m=[0.10],
        peer_quality_series_1m=[0.8],
    )
    assert P_extreme == pytest.approx(1.0), "Expected progress clipped to 1.0"

    # Very high novelty (should be clipped)
    _, N_extreme, _ = compute_components(
        gamma_avg_1m=0.70,
        gamma_avg_5m=0.70,
        eta_series_1m=[0.10],
        peer_quality_series_1m=[0.0, 1.0, 0.1, 0.9],  # Huge spread
    )
    assert N_extreme <= 1.0, "Novelty should be clipped to 1.0"

    # G* with extreme components
    params = GenerativityParams(alpha=1.0, beta=0.0, gamma=0.0)
    g = compute_gstar(params, 1.5, 0.0, 0.0)  # P > 1.0
    assert g <= 1.0, "G* should be clipped to 1.0"
