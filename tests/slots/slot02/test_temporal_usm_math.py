import math

import pytest

from nova.math.usm_temporal import TemporalUsmState, step_non_void, step_void


def test_step_non_void_initializes_from_instantaneous_values():
    """First non-VOID update initializes temporal state from instantaneous metrics."""
    state = step_non_void(
        prev=None,
        H_inst=1.5,
        rho_inst=0.7,
        C_inst=0.2,
        lambda_=0.6,
    )

    assert isinstance(state, TemporalUsmState)
    assert state.H == pytest.approx(1.5)
    assert state.rho == pytest.approx(0.7)
    assert state.C == pytest.approx(0.2)


def test_step_non_void_exponential_smoothing():
    """Non-VOID updates perform exponential smoothing over time."""
    prev = TemporalUsmState(H=1.0, rho=0.5, C=0.3)

    state = step_non_void(
        prev=prev,
        H_inst=2.0,
        rho_inst=0.8,
        C_inst=0.0,
        lambda_=0.4,
    )

    # Expected from spec: H_t = (1-λ)*H_prev + λ*H_inst
    assert state.H == pytest.approx((1 - 0.4) * 1.0 + 0.4 * 2.0)
    assert state.rho == pytest.approx((1 - 0.4) * 0.5 + 0.4 * 0.8)
    assert state.C == pytest.approx((1 - 0.4) * 0.3 + 0.4 * 0.0)


def test_step_void_soft_decay_toward_equilibrium():
    """VOID updates decay H and C while rho drifts toward rho_eq."""
    prev = TemporalUsmState(H=1.0, rho=0.2, C=0.5)
    lambda_ = 0.5
    rho_eq = 1.0

    state = step_void(prev=prev, lambda_=lambda_, rho_eq=rho_eq)

    assert state.H == pytest.approx(prev.H * lambda_)
    assert state.C == pytest.approx(prev.C * lambda_)
    expected_rho = prev.rho * lambda_ + (1 - lambda_) * rho_eq
    assert state.rho == pytest.approx(expected_rho)


def test_step_void_repeated_converges_to_equilibrium():
    """Repeated VOID updates converge: H,C → 0, rho → rho_eq."""
    state = TemporalUsmState(H=1.0, rho=0.2, C=0.5)
    lambda_ = 0.6
    rho_eq = 1.0

    for _ in range(10):
        state = step_void(prev=state, lambda_=lambda_, rho_eq=rho_eq)

    # With lambda=0.6, 10 steps yields H,C ~= 0.006
    assert state.H == pytest.approx(0.0, abs=1e-2)
    assert state.C == pytest.approx(0.0, abs=1e-2)
    assert state.rho == pytest.approx(rho_eq, rel=1e-2)


def test_invalid_lambda_raises_value_error():
    """lambda outside (0,1) is rejected to prevent unstable dynamics."""
    prev = TemporalUsmState(H=1.0, rho=0.5, C=0.3)

    for bad_lambda in [0.0, 1.0, -0.1, 1.5]:
        with pytest.raises(ValueError):
            step_non_void(prev=prev, H_inst=1.0, rho_inst=0.5, C_inst=0.3, lambda_=bad_lambda)
        with pytest.raises(ValueError):
            step_void(prev=prev, lambda_=bad_lambda, rho_eq=1.0)
