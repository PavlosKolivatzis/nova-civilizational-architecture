"""Test eigenvalue computation for 3×3 reduced system."""

import numpy as np
import pytest

from nova.adaptive_wisdom_core import Params3D, State3D, ThreeDProvider
from nova.bifurcation_monitor import BifurcationMonitor


def test_jacobian_structure():
    """Verify Jacobian has expected block structure."""
    params = Params3D(Q=0.7, S_ref=0.05, a1=0.2, a2=0.1, k_p=0.3, k_d=0.15)
    provider = ThreeDProvider(params)
    state = State3D(gamma=0.7, S=0.05, eta=0.10)

    J = provider.jacobian(state)

    assert J.shape == (3, 3)
    # First row: [-eta, 0, 0]
    assert J[0, 0] == pytest.approx(-0.10)
    assert J[0, 1] == pytest.approx(0.0)
    assert J[0, 2] == pytest.approx(0.0)

    # Second row: [0, -a1, -a2]
    assert J[1, 0] == pytest.approx(0.0)
    assert J[1, 1] == pytest.approx(-0.2)
    assert J[1, 2] == pytest.approx(-0.1)

    # Third row: [0, k_p, -k_d]
    assert J[2, 0] == pytest.approx(0.0)
    assert J[2, 1] == pytest.approx(0.3)
    assert J[2, 2] == pytest.approx(-0.15)


def test_eigenvalues_stable_case():
    """Test eigenvalues for stable parameter set."""
    params = Params3D(Q=0.7, S_ref=0.05, a1=0.2, a2=0.1, k_p=0.3, k_d=0.15)
    provider = ThreeDProvider(params)
    state = State3D(gamma=0.7, S=0.05, eta=0.10)

    J = provider.jacobian(state)
    eigs = np.linalg.eigvals(J)

    # All real parts should be negative (stable)
    assert all(np.real(lam) < 0 for lam in eigs)

    # One eigenvalue should be -eta
    assert any(np.isclose(lam, -0.10, atol=1e-6) for lam in eigs)


def test_bifurcation_monitor_stable():
    """Test bifurcation monitor on stable system."""
    params = Params3D(Q=0.7, S_ref=0.05, a1=0.2, a2=0.1, k_p=0.3, k_d=0.15)
    provider = ThreeDProvider(params)
    state = State3D(gamma=0.7, S=0.05, eta=0.10)

    J = provider.jacobian(state)
    monitor = BifurcationMonitor(hopf_threshold=0.02)
    analysis = monitor.analyze(J)

    # Should be stable
    assert analysis.stable
    assert analysis.S > 0

    # Should not have Hopf risk
    assert not analysis.hopf_risk

    # Spectral radius should be < 1 for stable system
    assert analysis.rho < 1.0


def test_bifurcation_monitor_near_hopf():
    """Test detection of near-Hopf conditions."""
    # Reduce k_d to push toward Hopf
    params = Params3D(Q=0.7, S_ref=0.05, a1=0.2, a2=0.1, k_p=0.5, k_d=0.05)
    provider = ThreeDProvider(params)
    state = State3D(gamma=0.7, S=0.05, eta=0.10)

    J = provider.jacobian(state)
    monitor = BifurcationMonitor(hopf_threshold=0.02)
    analysis = monitor.analyze(J)

    # May or may not be stable depending on exact parameters
    # But should detect oscillatory modes
    assert len(analysis.oscillatory_freqs) > 0

    # Hopf distance should be small
    assert analysis.H < 0.1


def test_metrics_rho_S_H():
    """Verify ρ, S, H computation from eigenvalues."""
    params = Params3D(Q=0.7, S_ref=0.05, a1=0.2, a2=0.1, k_p=0.3, k_d=0.15)
    provider = ThreeDProvider(params)
    state = State3D(gamma=0.7, S=0.05, eta=0.10)

    J = provider.jacobian(state)
    eigs = np.linalg.eigvals(J)

    monitor = BifurcationMonitor()
    analysis = monitor.analyze(J)

    # ρ = max|λ|
    expected_rho = np.max(np.abs(eigs))
    assert analysis.rho == pytest.approx(expected_rho, rel=1e-6)

    # S = -max Re(λ)
    expected_S = -np.max(np.real(eigs))
    assert analysis.S == pytest.approx(expected_S, rel=1e-6)

    # Both should be positive for stable system
    assert analysis.rho > 0
    assert analysis.S > 0


def test_params_from_env(monkeypatch):
    """Test parameter loading from environment."""
    monkeypatch.setenv("NOVA_WISDOM_Q", "0.8")
    monkeypatch.setenv("NOVA_WISDOM_S_REF", "0.06")
    monkeypatch.setenv("NOVA_WISDOM_A1", "0.25")

    params = Params3D.from_env()

    assert params.Q == pytest.approx(0.8)
    assert params.S_ref == pytest.approx(0.06)
    assert params.a1 == pytest.approx(0.25)
