"""Integration tests for ORP in Slot10 Gatekeeper - Phase 11.2

Tests verify ORP posture adjustments in deployment gate decisions:
- deployment_freeze blocks deployments in controlled_degradation and higher regimes
- emergency/recovery regimes log rollback warnings
- ORP metadata recorded in gate results
- Flag gating (NOVA_ENABLE_ORP) behavior
"""

import pytest
from unittest.mock import patch, MagicMock
from src.nova.slots.slot10_civilizational_deployment.core.gatekeeper import Gatekeeper, GateResult
from src.nova.slots.slot10_civilizational_deployment.core.policy import Slot10Policy


@pytest.fixture
def mock_orp_normal_regime():
    """Mock ORP returning normal regime."""
    return {
        "regime": "normal",
        "regime_score": 0.15,
        "posture_adjustments": {
            "threshold_multiplier": 1.0,
            "traffic_limit": 1.0,
            "deployment_freeze": False,
            "safe_mode_forced": False,
        },
    }


@pytest.fixture
def mock_orp_heightened_regime():
    """Mock ORP returning heightened regime."""
    return {
        "regime": "heightened",
        "regime_score": 0.38,
        "posture_adjustments": {
            "threshold_multiplier": 0.85,
            "traffic_limit": 0.90,
            "deployment_freeze": False,
            "safe_mode_forced": False,
        },
    }


@pytest.fixture
def mock_orp_controlled_degradation_regime():
    """Mock ORP returning controlled_degradation regime."""
    return {
        "regime": "controlled_degradation",
        "regime_score": 0.58,
        "posture_adjustments": {
            "threshold_multiplier": 0.70,
            "traffic_limit": 0.60,
            "deployment_freeze": True,  # Deployments blocked
            "safe_mode_forced": False,
        },
    }


@pytest.fixture
def mock_orp_emergency_regime():
    """Mock ORP returning emergency_stabilization regime."""
    return {
        "regime": "emergency_stabilization",
        "regime_score": 0.76,
        "posture_adjustments": {
            "threshold_multiplier": 0.60,
            "traffic_limit": 0.30,
            "deployment_freeze": True,
            "safe_mode_forced": True,
        },
    }


@pytest.fixture
def mock_orp_recovery_regime():
    """Mock ORP returning recovery regime."""
    return {
        "regime": "recovery",
        "regime_score": 0.91,
        "posture_adjustments": {
            "threshold_multiplier": 0.50,
            "traffic_limit": 0.10,
            "deployment_freeze": True,
            "safe_mode_forced": True,
        },
    }


@pytest.fixture
def gatekeeper():
    """Create Gatekeeper instance."""
    return Gatekeeper(policy=Slot10Policy())


# ---------- Deployment Freeze Tests ----------


def test_orp_normal_allows_deployments(gatekeeper, mock_orp_normal_regime):
    """Test normal regime allows deployments (deployment_freeze=False)."""
    with patch("src.nova.slots.slot10_civilizational_deployment.core.gatekeeper._orp_enabled", return_value=True), \
         patch("src.nova.slots.slot10_civilizational_deployment.core.gatekeeper.get_operational_regime", return_value=mock_orp_normal_regime), \
         patch("src.nova.slots.slot10_civilizational_deployment.core.gatekeeper.record_orp"):

        slot08 = {"quarantine_active": False, "integrity_score": 0.9, "recent_recoveries": {"success_rate_5m": 0.95}}
        slot04 = {"safe_mode_active": False, "drift_z": 0.5}

        result = gatekeeper.evaluate_deploy_gate(slot08=slot08, slot04=slot04)

        assert result.passed is True
        assert "orp_deployment_freeze" not in result.failed_conditions
        assert result.health_snapshot["orp"]["regime"] == "normal"


def test_orp_heightened_allows_deployments(gatekeeper, mock_orp_heightened_regime):
    """Test heightened regime still allows deployments."""
    with patch("src.nova.slots.slot10_civilizational_deployment.core.gatekeeper._orp_enabled", return_value=True), \
         patch("src.nova.slots.slot10_civilizational_deployment.core.gatekeeper.get_operational_regime", return_value=mock_orp_heightened_regime), \
         patch("src.nova.slots.slot10_civilizational_deployment.core.gatekeeper.record_orp"):

        slot08 = {"quarantine_active": False, "integrity_score": 0.9, "recent_recoveries": {"success_rate_5m": 0.95}}
        slot04 = {"safe_mode_active": False, "drift_z": 0.5}

        result = gatekeeper.evaluate_deploy_gate(slot08=slot08, slot04=slot04)

        assert result.passed is True
        assert "orp_deployment_freeze" not in result.failed_conditions


def test_orp_controlled_degradation_blocks_deployments(gatekeeper, mock_orp_controlled_degradation_regime):
    """Test controlled_degradation regime blocks deployments."""
    with patch("src.nova.slots.slot10_civilizational_deployment.core.gatekeeper._orp_enabled", return_value=True), \
         patch("src.nova.slots.slot10_civilizational_deployment.core.gatekeeper.get_operational_regime", return_value=mock_orp_controlled_degradation_regime), \
         patch("src.nova.slots.slot10_civilizational_deployment.core.gatekeeper.record_orp"):

        slot08 = {"quarantine_active": False, "integrity_score": 0.9, "recent_recoveries": {"success_rate_5m": 0.95}}
        slot04 = {"safe_mode_active": False, "drift_z": 0.5}

        result = gatekeeper.evaluate_deploy_gate(slot08=slot08, slot04=slot04)

        assert result.passed is False
        assert "orp_deployment_freeze" in result.failed_conditions
        assert result.health_snapshot["orp"]["regime"] == "controlled_degradation"


def test_orp_emergency_blocks_deployments(gatekeeper, mock_orp_emergency_regime):
    """Test emergency regime blocks deployments and logs warning."""
    with patch("src.nova.slots.slot10_civilizational_deployment.core.gatekeeper._orp_enabled", return_value=True), \
         patch("src.nova.slots.slot10_civilizational_deployment.core.gatekeeper.get_operational_regime", return_value=mock_orp_emergency_regime), \
         patch("src.nova.slots.slot10_civilizational_deployment.core.gatekeeper.record_orp"), \
         patch("src.nova.slots.slot10_civilizational_deployment.core.gatekeeper.logger") as mock_logger:

        slot08 = {"quarantine_active": False, "integrity_score": 0.9, "recent_recoveries": {"success_rate_5m": 0.95}}
        slot04 = {"safe_mode_active": False, "drift_z": 0.5}

        result = gatekeeper.evaluate_deploy_gate(slot08=slot08, slot04=slot04)

        assert result.passed is False
        assert "orp_deployment_freeze" in result.failed_conditions
        # Check rollback warning logged (may be multiple warnings)
        assert mock_logger.warning.call_count >= 1
        # Verify ORP rollback warning is in the calls
        warning_calls = [str(call) for call in mock_logger.warning.call_args_list]
        assert any("recommends rollback" in call for call in warning_calls)


def test_orp_recovery_blocks_deployments(gatekeeper, mock_orp_recovery_regime):
    """Test recovery regime blocks deployments and logs warning."""
    with patch("src.nova.slots.slot10_civilizational_deployment.core.gatekeeper._orp_enabled", return_value=True), \
         patch("src.nova.slots.slot10_civilizational_deployment.core.gatekeeper.get_operational_regime", return_value=mock_orp_recovery_regime), \
         patch("src.nova.slots.slot10_civilizational_deployment.core.gatekeeper.record_orp"), \
         patch("src.nova.slots.slot10_civilizational_deployment.core.gatekeeper.logger") as mock_logger:

        slot08 = {"quarantine_active": False, "integrity_score": 0.9, "recent_recoveries": {"success_rate_5m": 0.95}}
        slot04 = {"safe_mode_active": False, "drift_z": 0.5}

        result = gatekeeper.evaluate_deploy_gate(slot08=slot08, slot04=slot04)

        assert result.passed is False
        assert "orp_deployment_freeze" in result.failed_conditions
        assert result.health_snapshot["orp"]["regime"] == "recovery"
        # Verify rollback warning (may be multiple warnings)
        assert mock_logger.warning.call_count >= 1
        warning_calls = [str(call) for call in mock_logger.warning.call_args_list]
        assert any("recommends rollback" in call for call in warning_calls)


# ---------- ORP Metadata Recording ----------


def test_orp_metadata_recorded_in_health_snapshot(gatekeeper, mock_orp_heightened_regime):
    """Test ORP snapshot included in gate result health_snapshot."""
    with patch("src.nova.slots.slot10_civilizational_deployment.core.gatekeeper._orp_enabled", return_value=True), \
         patch("src.nova.slots.slot10_civilizational_deployment.core.gatekeeper.get_operational_regime", return_value=mock_orp_heightened_regime), \
         patch("src.nova.slots.slot10_civilizational_deployment.core.gatekeeper.record_orp"):

        slot08 = {"quarantine_active": False, "integrity_score": 0.9, "recent_recoveries": {"success_rate_5m": 0.95}}
        slot04 = {"safe_mode_active": False, "drift_z": 0.5}

        result = gatekeeper.evaluate_deploy_gate(slot08=slot08, slot04=slot04)

        assert "orp" in result.health_snapshot
        orp_snapshot = result.health_snapshot["orp"]
        assert orp_snapshot["regime"] == "heightened"
        assert orp_snapshot["regime_score"] == 0.38
        assert "posture_adjustments" in orp_snapshot


def test_orp_metrics_recorded_via_record_orp(gatekeeper, mock_orp_normal_regime):
    """Test record_orp() called with ORP snapshot."""
    with patch("src.nova.slots.slot10_civilizational_deployment.core.gatekeeper._orp_enabled", return_value=True), \
         patch("src.nova.slots.slot10_civilizational_deployment.core.gatekeeper.get_operational_regime", return_value=mock_orp_normal_regime) as mock_get, \
         patch("src.nova.slots.slot10_civilizational_deployment.core.gatekeeper.record_orp") as mock_record:

        slot08 = {"quarantine_active": False, "integrity_score": 0.9, "recent_recoveries": {"success_rate_5m": 0.95}}
        slot04 = {"safe_mode_active": False, "drift_z": 0.5}

        gatekeeper.evaluate_deploy_gate(slot08=slot08, slot04=slot04)

        # Verify record_orp called
        mock_record.assert_called_once_with(mock_orp_normal_regime)


# ---------- Flag Gating Tests ----------


def test_orp_disabled_no_deployment_freeze(gatekeeper):
    """Test NOVA_ENABLE_ORP=0 does not apply deployment_freeze."""
    with patch("src.nova.slots.slot10_civilizational_deployment.core.gatekeeper._orp_enabled", return_value=False), \
         patch("src.nova.slots.slot10_civilizational_deployment.core.gatekeeper.get_operational_regime") as mock_get:

        slot08 = {"quarantine_active": False, "integrity_score": 0.9, "recent_recoveries": {"success_rate_5m": 0.95}}
        slot04 = {"safe_mode_active": False, "drift_z": 0.5}

        result = gatekeeper.evaluate_deploy_gate(slot08=slot08, slot04=slot04)

        # ORP should not be called
        mock_get.assert_not_called()
        # No ORP-related failures
        assert "orp_deployment_freeze" not in result.failed_conditions


def test_orp_exception_does_not_crash_gatekeeper(gatekeeper):
    """Test ORP exception handled gracefully, gate evaluation continues."""
    with patch("src.nova.slots.slot10_civilizational_deployment.core.gatekeeper._orp_enabled", return_value=True), \
         patch("src.nova.slots.slot10_civilizational_deployment.core.gatekeeper.get_operational_regime", side_effect=Exception("ORP failed")), \
         patch("src.nova.slots.slot10_civilizational_deployment.core.gatekeeper.record_orp"):

        slot08 = {"quarantine_active": False, "integrity_score": 0.9, "recent_recoveries": {"success_rate_5m": 0.95}}
        slot04 = {"safe_mode_active": False, "drift_z": 0.5}

        result = gatekeeper.evaluate_deploy_gate(slot08=slot08, slot04=slot04)

        # Gate evaluation should succeed without ORP
        assert isinstance(result, GateResult)
        assert result.passed is True


# ---------- Combined Gate Scenarios ----------


def test_orp_deployment_freeze_overrides_slot08_pass(gatekeeper, mock_orp_controlled_degradation_regime):
    """Test ORP deployment_freeze blocks even when Slot08/Slot04 gates pass."""
    with patch("src.nova.slots.slot10_civilizational_deployment.core.gatekeeper._orp_enabled", return_value=True), \
         patch("src.nova.slots.slot10_civilizational_deployment.core.gatekeeper.get_operational_regime", return_value=mock_orp_controlled_degradation_regime), \
         patch("src.nova.slots.slot10_civilizational_deployment.core.gatekeeper.record_orp"):

        # All other gates pass
        slot08 = {"quarantine_active": False, "integrity_score": 0.95, "recent_recoveries": {"success_rate_5m": 0.98}}
        slot04 = {"safe_mode_active": False, "drift_z": 0.3}

        result = gatekeeper.evaluate_deploy_gate(slot08=slot08, slot04=slot04)

        # ORP should still block
        assert result.passed is False
        assert "orp_deployment_freeze" in result.failed_conditions
        # Other gates should not fail
        assert "slot08_quarantine" not in result.failed_conditions
        assert "slot04_safe_mode" not in result.failed_conditions


def test_orp_plus_slot08_failure_both_in_failed_conditions(gatekeeper, mock_orp_controlled_degradation_regime):
    """Test multiple gate failures (ORP + Slot08) recorded together."""
    with patch("src.nova.slots.slot10_civilizational_deployment.core.gatekeeper._orp_enabled", return_value=True), \
         patch("src.nova.slots.slot10_civilizational_deployment.core.gatekeeper.get_operational_regime", return_value=mock_orp_controlled_degradation_regime), \
         patch("src.nova.slots.slot10_civilizational_deployment.core.gatekeeper.record_orp"):

        # Slot08 quarantine active + ORP freeze
        slot08 = {"quarantine_active": True, "integrity_score": 0.95, "recent_recoveries": {"success_rate_5m": 0.98}}
        slot04 = {"safe_mode_active": False, "drift_z": 0.3}

        result = gatekeeper.evaluate_deploy_gate(slot08=slot08, slot04=slot04)

        assert result.passed is False
        assert "orp_deployment_freeze" in result.failed_conditions
        assert "slot08_quarantine" in result.failed_conditions


# ---------- Edge Cases ----------


def test_orp_missing_posture_adjustments_uses_defaults(gatekeeper):
    """Test missing posture_adjustments uses safe defaults (no freeze)."""
    orp_snapshot = {
        "regime": "normal",
        "regime_score": 0.15,
        # Missing posture_adjustments
    }

    with patch("src.nova.slots.slot10_civilizational_deployment.core.gatekeeper._orp_enabled", return_value=True), \
         patch("src.nova.slots.slot10_civilizational_deployment.core.gatekeeper.get_operational_regime", return_value=orp_snapshot), \
         patch("src.nova.slots.slot10_civilizational_deployment.core.gatekeeper.record_orp"):

        slot08 = {"quarantine_active": False, "integrity_score": 0.9, "recent_recoveries": {"success_rate_5m": 0.95}}
        slot04 = {"safe_mode_active": False, "drift_z": 0.5}

        result = gatekeeper.evaluate_deploy_gate(slot08=slot08, slot04=slot04)

        # Should not freeze (default=False)
        assert result.passed is True
        assert "orp_deployment_freeze" not in result.failed_conditions


def test_orp_empty_snapshot_uses_defaults(gatekeeper):
    """Test empty ORP snapshot handled gracefully."""
    with patch("src.nova.slots.slot10_civilizational_deployment.core.gatekeeper._orp_enabled", return_value=True), \
         patch("src.nova.slots.slot10_civilizational_deployment.core.gatekeeper.get_operational_regime", return_value={}), \
         patch("src.nova.slots.slot10_civilizational_deployment.core.gatekeeper.record_orp"):

        slot08 = {"quarantine_active": False, "integrity_score": 0.9, "recent_recoveries": {"success_rate_5m": 0.95}}
        slot04 = {"safe_mode_active": False, "drift_z": 0.5}

        result = gatekeeper.evaluate_deploy_gate(slot08=slot08, slot04=slot04)

        # Should not crash, defaults to normal regime behavior
        assert isinstance(result, GateResult)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
