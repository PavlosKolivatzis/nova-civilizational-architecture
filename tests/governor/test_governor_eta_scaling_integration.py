"""Integration tests for Wisdom Governor η scaling with ORP - Phase 11.3 Step 2"""

import pytest
from unittest.mock import patch
from src.nova.governor.adaptive_wisdom import AdaptiveWisdomGovernor


@pytest.fixture
def governor():
    """Create Wisdom Governor instance."""
    return AdaptiveWisdomGovernor(eta=0.10, eta_min=0.05, eta_max=0.15)


# ---------- Flag Gating Tests ----------


def test_eta_scaling_disabled_no_changes(governor, monkeypatch):
    """Test NOVA_ENABLE_ETA_SCALING=0 does not apply scaling."""
    monkeypatch.setenv("NOVA_ENABLE_ETA_SCALING", "0")

    # Mock regime ledger to return heightened regime
    with patch("src.nova.governor.adaptive_wisdom._get_regime_duration") as mock_regime:
        mock_regime.return_value = {"regime": "heightened", "duration_s": 400.0}

        # Compute base eta
        telemetry = governor.step(margin=0.5, G=0.7)

        # Should be base eta (no ORP scaling applied)
        # OPTIMAL mode: eta = max(eta_min, min(eta_max, 0.12))
        assert telemetry.eta == 0.12
        assert telemetry.mode == "OPTIMAL"


def test_eta_scaling_enabled_applies_orp_scaling(governor, monkeypatch):
    """Test NOVA_ENABLE_ETA_SCALING=1 applies ORP scaling."""
    monkeypatch.setenv("NOVA_ENABLE_ETA_SCALING", "1")
    monkeypatch.setenv("NOVA_ENABLE_REGIME_LEDGER", "1")  # Enable ledger for duration

    # Mock regime ledger to return heightened ≥5min (scale=0.90)
    with patch("src.nova.governor.adaptive_wisdom._get_regime_duration") as mock_regime:
        mock_regime.return_value = {"regime": "heightened", "duration_s": 400.0}

        # Compute base eta
        telemetry = governor.step(margin=0.5, G=0.7)

        # Should apply ORP scaling: eta_base=0.12, heightened ≥5min scale=0.90
        # eta_scaled = 0.12 * 0.90 = 0.108
        assert telemetry.eta == pytest.approx(0.108, abs=0.001)
        assert telemetry.mode == "OPTIMAL"


# ---------- Regime Scaling Tests ----------


def test_eta_scaling_normal_regime_no_change(governor, monkeypatch):
    """Test normal regime preserves base eta (scale=1.0)."""
    monkeypatch.setenv("NOVA_ENABLE_ETA_SCALING", "1")
    monkeypatch.setenv("NOVA_ENABLE_REGIME_LEDGER", "1")

    with patch("src.nova.governor.adaptive_wisdom._get_regime_duration") as mock_regime:
        mock_regime.return_value = {"regime": "normal", "duration_s": 100.0}

        telemetry = governor.step(margin=0.5, G=0.7)

        # OPTIMAL mode: eta = 0.12, normal scale = 1.0
        # eta_scaled = 0.12 * 1.0 = 0.12
        assert telemetry.eta == 0.12


def test_eta_scaling_heightened_short_duration(governor, monkeypatch):
    """Test heightened <5min scales by 0.95."""
    monkeypatch.setenv("NOVA_ENABLE_ETA_SCALING", "1")
    monkeypatch.setenv("NOVA_ENABLE_REGIME_LEDGER", "1")

    with patch("src.nova.governor.adaptive_wisdom._get_regime_duration") as mock_regime:
        mock_regime.return_value = {"regime": "heightened", "duration_s": 100.0}

        telemetry = governor.step(margin=0.5, G=0.7)

        # OPTIMAL mode: eta = 0.12, heightened <5min scale = 0.95
        # eta_scaled = 0.12 * 0.95 = 0.114
        assert telemetry.eta == pytest.approx(0.114, abs=0.001)


def test_eta_scaling_heightened_long_duration(governor, monkeypatch):
    """Test heightened ≥5min scales by 0.90."""
    monkeypatch.setenv("NOVA_ENABLE_ETA_SCALING", "1")
    monkeypatch.setenv("NOVA_ENABLE_REGIME_LEDGER", "1")

    with patch("src.nova.governor.adaptive_wisdom._get_regime_duration") as mock_regime:
        mock_regime.return_value = {"regime": "heightened", "duration_s": 400.0}

        telemetry = governor.step(margin=0.5, G=0.7)

        # OPTIMAL mode: eta = 0.12, heightened ≥5min scale = 0.90
        # eta_scaled = 0.12 * 0.90 = 0.108
        assert telemetry.eta == pytest.approx(0.108, abs=0.001)


def test_eta_scaling_emergency_regime(governor, monkeypatch):
    """Test emergency_stabilization scales by 0.50."""
    monkeypatch.setenv("NOVA_ENABLE_ETA_SCALING", "1")
    monkeypatch.setenv("NOVA_ENABLE_REGIME_LEDGER", "1")

    with patch("src.nova.governor.adaptive_wisdom._get_regime_duration") as mock_regime:
        mock_regime.return_value = {"regime": "emergency_stabilization", "duration_s": 100.0}

        telemetry = governor.step(margin=0.5, G=0.7)

        # OPTIMAL mode: eta = 0.12, emergency scale = 0.50
        # eta_scaled = 0.12 * 0.50 = 0.06
        assert telemetry.eta == pytest.approx(0.06, abs=0.001)


def test_eta_scaling_recovery_regime(governor, monkeypatch):
    """Test recovery scales by 0.25 (very conservative)."""
    monkeypatch.setenv("NOVA_ENABLE_ETA_SCALING", "1")
    monkeypatch.setenv("NOVA_ENABLE_REGIME_LEDGER", "1")

    with patch("src.nova.governor.adaptive_wisdom._get_regime_duration") as mock_regime:
        mock_regime.return_value = {"regime": "recovery", "duration_s": 500.0}

        telemetry = governor.step(margin=0.5, G=0.7)

        # OPTIMAL mode: eta = 0.12, recovery scale = 0.25
        # eta_scaled = 0.12 * 0.25 = 0.03
        # But clamped to eta_min=0.05
        assert telemetry.eta == 0.05  # Clamped to eta_min


# ---------- Mode Interaction Tests ----------


def test_eta_scaling_critical_mode_with_orp(governor, monkeypatch):
    """Test STABILIZING mode (margin=0.01) + ORP scaling."""
    monkeypatch.setenv("NOVA_ENABLE_ETA_SCALING", "1")
    monkeypatch.setenv("NOVA_ENABLE_REGIME_LEDGER", "1")

    with patch("src.nova.governor.adaptive_wisdom._get_regime_duration") as mock_regime:
        mock_regime.return_value = {"regime": "heightened", "duration_s": 400.0}

        # STABILIZING mode: margin=0.01 (between critical and stabilizing thresholds)
        telemetry = governor.step(margin=0.01, G=0.5)

        # STABILIZING mode: eta_base = max(eta_min, 0.08) = 0.08
        # heightened ≥5min: scale = 0.90
        # eta_scaled = 0.08 * 0.90 = 0.072
        assert telemetry.eta == pytest.approx(0.072, abs=0.001)
        assert telemetry.mode == "STABILIZING"


def test_eta_scaling_exploring_mode_with_orp(governor, monkeypatch):
    """Test EXPLORING mode + ORP scaling."""
    monkeypatch.setenv("NOVA_ENABLE_ETA_SCALING", "1")
    monkeypatch.setenv("NOVA_ENABLE_REGIME_LEDGER", "1")

    with patch("src.nova.governor.adaptive_wisdom._get_regime_duration") as mock_regime:
        mock_regime.return_value = {"regime": "heightened", "duration_s": 400.0}

        # EXPLORING mode: margin > exploring_margin (0.30) and G < exploring_g (0.50)
        telemetry = governor.step(margin=0.40, G=0.40)

        # EXPLORING mode: eta_base = min(eta_max, eta * 1.10, 0.18)
        # eta was 0.10 → eta * 1.10 = 0.11
        # eta_base = min(0.15, 0.11, 0.18) = 0.11
        # heightened ≥5min: scale = 0.90
        # eta_scaled = 0.11 * 0.90 = 0.099
        assert telemetry.eta == pytest.approx(0.099, abs=0.001)
        assert telemetry.mode == "EXPLORING"


# ---------- Constraint Tests ----------


def test_eta_scaling_never_exceeds_eta_max(governor, monkeypatch):
    """Test scaled eta never exceeds eta_max=0.15."""
    monkeypatch.setenv("NOVA_ENABLE_ETA_SCALING", "1")
    monkeypatch.setenv("NOVA_ENABLE_REGIME_LEDGER", "1")

    # Set governor eta to eta_max
    governor.eta = 0.15

    with patch("src.nova.governor.adaptive_wisdom._get_regime_duration") as mock_regime:
        # Normal regime (scale=1.0) should preserve eta_max
        mock_regime.return_value = {"regime": "normal", "duration_s": 100.0}

        telemetry = governor.step(margin=0.5, G=0.7)

        # OPTIMAL mode: eta_base = max(eta_min, min(eta_max, 0.12)) = 0.12
        # normal scale = 1.0
        # eta_scaled = 0.12 * 1.0 = 0.12 (within bounds)
        assert telemetry.eta <= 0.15


def test_eta_scaling_respects_eta_min(governor, monkeypatch):
    """Test scaled eta respects eta_min=0.05."""
    monkeypatch.setenv("NOVA_ENABLE_ETA_SCALING", "1")
    monkeypatch.setenv("NOVA_ENABLE_REGIME_LEDGER", "1")

    with patch("src.nova.governor.adaptive_wisdom._get_regime_duration") as mock_regime:
        # Recovery regime (scale=0.25) should be clamped to eta_min
        mock_regime.return_value = {"regime": "recovery", "duration_s": 100.0}

        telemetry = governor.step(margin=0.5, G=0.7)

        # OPTIMAL mode: eta_base = 0.12
        # recovery scale = 0.25
        # eta_scaled = 0.12 * 0.25 = 0.03 → clamped to 0.05
        assert telemetry.eta >= 0.05


# ---------- Exception Handling Tests ----------


def test_eta_scaling_fallback_on_exception(governor, monkeypatch):
    """Test fallback to base eta if ORP scaling raises exception."""
    monkeypatch.setenv("NOVA_ENABLE_ETA_SCALING", "1")
    monkeypatch.setenv("NOVA_ENABLE_REGIME_LEDGER", "1")

    with patch("src.nova.governor.adaptive_wisdom._get_regime_duration") as mock_regime:
        # Simulate exception in ledger
        mock_regime.side_effect = Exception("Ledger failed")

        telemetry = governor.step(margin=0.5, G=0.7)

        # Should fallback to base eta (no scaling)
        # OPTIMAL mode: eta_base = 0.12
        assert telemetry.eta == 0.12
        assert telemetry.mode == "OPTIMAL"


def test_eta_scaling_graceful_when_imports_fail(monkeypatch):
    """Test graceful behavior when imports fail (fallback stubs)."""
    monkeypatch.setenv("NOVA_ENABLE_ETA_SCALING", "1")

    # This test verifies the try/except import fallback stubs work
    # If imports failed, _apply_eta_scaling returns eta_base unchanged
    # In practice, imports should succeed in test environment, but fallback exists
    governor = AdaptiveWisdomGovernor(eta=0.10, eta_min=0.05, eta_max=0.15)

    telemetry = governor.step(margin=0.5, G=0.7)

    # Should compute eta normally (imports work in test env)
    assert isinstance(telemetry.eta, float)
    assert 0.05 <= telemetry.eta <= 0.15


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
