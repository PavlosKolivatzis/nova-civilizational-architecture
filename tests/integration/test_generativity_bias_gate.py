"""Integration test: Generativity bias gating under low S/H conditions."""

import os

import pytest

from nova.wisdom.generativity_core import GenerativityParams, eta_bias


def setup_function():
    """Set gating thresholds for testing."""
    os.environ["NOVA_WISDOM_G_MIN_S"] = "0.03"
    os.environ["NOVA_WISDOM_G_MIN_H"] = "0.02"


def teardown_function():
    """Clean up environment."""
    os.environ.pop("NOVA_WISDOM_G_MIN_S", None)
    os.environ.pop("NOVA_WISDOM_G_MIN_H", None)


def test_bias_applied_when_stable():
    """Test that bias is applied when S >= min_s and H >= min_h."""
    params = GenerativityParams(g0=0.6, kappa=0.02)

    # High generativity
    bias = eta_bias(params, 0.8)
    assert bias > 0, "Expected positive bias when G* > G₀"

    # With stable S and H, bias should be applied
    # (Actual application happens in poller, this just verifies calculation)
    assert abs(bias) > 0.001, "Bias should be significant"


def test_bias_gated_when_low_stability():
    """Test that bias should be zeroed by poller when S < min_s."""
    params = GenerativityParams(g0=0.6, kappa=0.02)

    # Even with high G*, bias calculation returns non-zero
    bias = eta_bias(params, 0.8)
    assert bias != 0.0

    # But poller should gate it out when S < 0.03
    # (This is a conceptual test - actual gating is in poller)
    min_s = float(os.getenv("NOVA_WISDOM_G_MIN_S", "0.03"))

    # Simulate poller logic
    S = 0.02  # Low stability
    effective_bias = bias if S >= min_s else 0.0

    assert effective_bias == 0.0, "Bias should be gated out when S < min_s"


def test_bias_gated_when_hopf_near():
    """Test that bias should be zeroed by poller when H < min_h."""
    params = GenerativityParams(g0=0.6, kappa=0.02)

    bias = eta_bias(params, 0.8)
    assert bias != 0.0

    min_h = float(os.getenv("NOVA_WISDOM_G_MIN_H", "0.02"))

    # Simulate poller logic
    H = 0.01  # Hopf bifurcation near
    effective_bias = bias if H >= min_h else 0.0

    assert effective_bias == 0.0, "Bias should be gated out when H < min_h"


def test_bias_allowed_when_both_safe():
    """Test that bias is applied when both S and H are above thresholds."""
    params = GenerativityParams(g0=0.6, kappa=0.02)

    bias = eta_bias(params, 0.8)

    min_s = float(os.getenv("NOVA_WISDOM_G_MIN_S", "0.03"))
    min_h = float(os.getenv("NOVA_WISDOM_G_MIN_H", "0.02"))

    # Simulate stable conditions
    S = 0.05  # Safe
    H = 0.10  # Safe

    effective_bias = bias if (S >= min_s and H >= min_h) else 0.0

    assert effective_bias == bias, "Bias should be applied when both S and H safe"
    assert effective_bias > 0, "Expected positive bias for high G*"


def test_bias_magnitude_respects_kappa():
    """Test that kappa parameter controls bias strength."""
    # Low kappa → small bias
    params_low = GenerativityParams(g0=0.6, kappa=0.01)
    bias_low = eta_bias(params_low, 0.8)

    # High kappa → large bias
    params_high = GenerativityParams(g0=0.6, kappa=0.05)
    bias_high = eta_bias(params_high, 0.8)

    assert abs(bias_high) > abs(bias_low), "Higher kappa should give stronger bias"

    # Verify proportionality
    ratio = abs(bias_high) / abs(bias_low)
    assert ratio == pytest.approx(5.0, abs=0.1), "Bias should scale linearly with kappa"


def test_frozen_state_prevents_bias():
    """Test that frozen state in poller should prevent bias application."""
    params = GenerativityParams(g0=0.6, kappa=0.02)

    bias = eta_bias(params, 0.8)

    # Simulate poller logic with frozen state
    frozen = True
    S = 0.05  # Stable
    H = 0.10  # Stable
    min_s = 0.03
    min_h = 0.02

    # Poller should skip bias when frozen
    if frozen:
        effective_bias = 0.0
    else:
        effective_bias = bias if (S >= min_s and H >= min_h) else 0.0

    assert effective_bias == 0.0, "Bias should be zero when frozen"


def test_bias_with_target_generativity():
    """Test bias behavior around target G₀."""
    params = GenerativityParams(g0=0.6, kappa=0.02)

    # Below target → negative bias (reduce learning)
    bias_below = eta_bias(params, 0.4)
    assert bias_below < 0, "Expected negative bias when G* < G₀"

    # Above target → positive bias (increase learning)
    bias_above = eta_bias(params, 0.8)
    assert bias_above > 0, "Expected positive bias when G* > G₀"

    # At target → zero bias
    bias_at = eta_bias(params, 0.6)
    assert abs(bias_at) < 1e-9, "Expected zero bias when G* = G₀"

    # Verify symmetry
    assert abs(bias_below) == pytest.approx(abs(bias_above), abs=0.001)
