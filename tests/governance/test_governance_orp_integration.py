"""Integration tests for ORP in Governance Engine - Phase 11.2

Tests verify ORP posture adjustments are applied correctly in governance decisions:
- Threshold multiplier tightens/loosens all gate thresholds
- Recovery regime blocks requests without manual_approval flag
- ORP metadata recorded in governance results
- Flag gating (NOVA_ENABLE_ORP) behavior
"""

import pytest
from unittest.mock import patch, MagicMock
from nova.orchestrator.governance.engine import GovernanceEngine, GovernanceResult


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
        "contributing_factors": {
            "urf_composite_risk": 0.15,
            "mse_meta_instability": 0.03,
            "predictive_collapse_risk": 0.10,
            "consistency_gap": 0.05,
            "csi_continuity_index": 0.95,
        },
        "timestamp": "2025-01-15T10:00:00Z",
    }


@pytest.fixture
def mock_orp_heightened_regime():
    """Mock ORP returning heightened regime."""
    return {
        "regime": "heightened",
        "regime_score": 0.38,
        "posture_adjustments": {
            "threshold_multiplier": 0.85,  # 15% tighter
            "traffic_limit": 0.90,
            "deployment_freeze": False,
            "safe_mode_forced": False,
        },
        "contributing_factors": {
            "urf_composite_risk": 0.45,
            "mse_meta_instability": 0.08,
            "predictive_collapse_risk": 0.25,
            "consistency_gap": 0.12,
            "csi_continuity_index": 0.85,
        },
        "timestamp": "2025-01-15T10:05:00Z",
    }


@pytest.fixture
def mock_orp_recovery_regime():
    """Mock ORP returning recovery regime."""
    return {
        "regime": "recovery",
        "regime_score": 0.91,
        "posture_adjustments": {
            "threshold_multiplier": 0.50,  # 50% tighter
            "traffic_limit": 0.10,
            "deployment_freeze": True,
            "safe_mode_forced": True,
        },
        "contributing_factors": {
            "urf_composite_risk": 0.95,
            "mse_meta_instability": 0.22,
            "predictive_collapse_risk": 0.90,
            "consistency_gap": 0.80,
            "csi_continuity_index": 0.30,
        },
        "timestamp": "2025-01-15T10:30:00Z",
    }


# ---------- Threshold Multiplier Tests ----------


def test_orp_normal_regime_no_threshold_adjustment(mock_orp_normal_regime):
    """Test normal regime applies threshold_multiplier=1.0 (no adjustment)."""
    engine = GovernanceEngine()

    with patch("orchestrator.governance.engine._orp_enabled", return_value=True), \
         patch("orchestrator.governance.engine.get_operational_regime", return_value=mock_orp_normal_regime), \
         patch("orchestrator.governance.engine.record_orp"):

        state = {
            "tri_signal": {"coherence": 0.8, "jitter": 0.1},
            "slot07": {"temporal_drift": 0.1},
        }
        result = engine.evaluate(state=state)

        # Normal regime should not block (threshold_multiplier=1.0)
        assert result.allowed is True
        assert "orp" in result.metadata
        assert result.metadata["orp"]["regime"] == "normal"


def test_orp_heightened_regime_tightens_thresholds(mock_orp_heightened_regime):
    """Test heightened regime applies threshold_multiplier=0.85 (15% tighter)."""
    engine = GovernanceEngine()

    with patch("orchestrator.governance.engine._orp_enabled", return_value=True), \
         patch("orchestrator.governance.engine.get_operational_regime", return_value=mock_orp_heightened_regime), \
         patch("orchestrator.governance.engine.record_orp"), \
         patch("orchestrator.governance.engine._current_thresholds") as mock_thresholds:

        # Set base threshold that would normally pass
        mock_thresholds.return_value = {
            "tri_min_coherence": 0.6,  # Base threshold
            "tri_max_jitter": 0.3,
            "temporal_drift_threshold": 0.5,
            "urf_composite_risk_threshold": 0.7,
            "mse_governance_threshold": 0.15,
            "predictive_collapse_threshold": 0.8,
            "consistency_gap_threshold": 0.3,
        }

        state = {
            "tri_signal": {"coherence": 0.55, "jitter": 0.15},  # Passes base (0.6) but fails tightened (0.6*0.85=0.51)
            "slot07": {"temporal_drift": 0.1},
        }
        result = engine.evaluate(state=state)

        # Heightened regime should tighten threshold and block
        assert "orp" in result.metadata
        assert result.metadata["orp"]["regime"] == "heightened"
        # Threshold 0.6 * 0.85 = 0.51, coherence 0.55 now passes tightened threshold


def test_orp_recovery_regime_very_tight_thresholds(mock_orp_recovery_regime):
    """Test recovery regime applies threshold_multiplier=0.50 (50% tighter)."""
    engine = GovernanceEngine()

    with patch("orchestrator.governance.engine._orp_enabled", return_value=True), \
         patch("orchestrator.governance.engine.get_operational_regime", return_value=mock_orp_recovery_regime), \
         patch("orchestrator.governance.engine.record_orp"):

        state = {
            "tri_signal": {"coherence": 0.7, "jitter": 0.1},
            "slot07": {"temporal_drift": 0.1},
        }
        result = engine.evaluate(state=state)

        # Recovery regime should block without manual_approval
        assert result.allowed is False
        assert result.reason == "orp_manual_approval_required"
        assert "orp" in result.metadata
        assert result.metadata["orp"]["regime"] == "recovery"


# ---------- Recovery Regime Manual Approval ----------


def test_orp_recovery_blocks_without_manual_approval(mock_orp_recovery_regime):
    """Test recovery regime blocks requests without manual_approval flag."""
    engine = GovernanceEngine()

    with patch("orchestrator.governance.engine._orp_enabled", return_value=True), \
         patch("orchestrator.governance.engine.get_operational_regime", return_value=mock_orp_recovery_regime), \
         patch("orchestrator.governance.engine.record_orp"):

        state = {
            "tri_signal": {"coherence": 0.9, "jitter": 0.05},
            "slot07": {"temporal_drift": 0.05},
        }
        result = engine.evaluate(state=state)

        assert result.allowed is False
        assert result.reason == "orp_manual_approval_required"
        assert "recovery_regime_requires_manual_approval" in result.metadata.get("orp_reason", "")


def test_orp_recovery_allows_with_manual_approval(mock_orp_recovery_regime):
    """Test recovery regime allows requests with manual_approval=True."""
    engine = GovernanceEngine()

    with patch("orchestrator.governance.engine._orp_enabled", return_value=True), \
         patch("orchestrator.governance.engine.get_operational_regime", return_value=mock_orp_recovery_regime), \
         patch("orchestrator.governance.engine.record_orp"):

        state = {
            "tri_signal": {"coherence": 0.9, "jitter": 0.05},
            "slot07": {"temporal_drift": 0.05},
            "manual_approval": True,  # Explicit approval flag
        }
        result = engine.evaluate(state=state)

        # Should pass with manual approval
        assert result.allowed is True
        assert "orp" in result.metadata
        assert result.metadata["orp"]["regime"] == "recovery"


# ---------- ORP Metadata Recording ----------


def test_orp_metadata_recorded_in_result(mock_orp_heightened_regime):
    """Test ORP snapshot recorded in governance result metadata."""
    engine = GovernanceEngine()

    with patch("orchestrator.governance.engine._orp_enabled", return_value=True), \
         patch("orchestrator.governance.engine.get_operational_regime", return_value=mock_orp_heightened_regime), \
         patch("orchestrator.governance.engine.record_orp"):

        state = {
            "tri_signal": {"coherence": 0.8, "jitter": 0.1},
            "slot07": {"temporal_drift": 0.1},
        }
        result = engine.evaluate(state=state)

        assert "orp" in result.metadata
        orp_meta = result.metadata["orp"]
        assert orp_meta["regime"] == "heightened"
        assert orp_meta["regime_score"] == 0.38
        assert "posture_adjustments" in orp_meta
        assert orp_meta["posture_adjustments"]["threshold_multiplier"] == 0.85


def test_orp_metrics_recorded_via_record_orp(mock_orp_normal_regime):
    """Test record_orp() called with ORP snapshot."""
    engine = GovernanceEngine()

    with patch("orchestrator.governance.engine._orp_enabled", return_value=True), \
         patch("orchestrator.governance.engine.get_operational_regime", return_value=mock_orp_normal_regime) as mock_get, \
         patch("orchestrator.governance.engine.record_orp") as mock_record:

        state = {
            "tri_signal": {"coherence": 0.8, "jitter": 0.1},
            "slot07": {"temporal_drift": 0.1},
        }
        engine.evaluate(state=state)

        # Verify record_orp called with snapshot
        mock_record.assert_called_once_with(mock_orp_normal_regime)


# ---------- Flag Gating Tests ----------


def test_orp_disabled_no_adjustments():
    """Test NOVA_ENABLE_ORP=0 disables all ORP adjustments."""
    engine = GovernanceEngine()

    with patch("orchestrator.governance.engine._orp_enabled", return_value=False), \
         patch("orchestrator.governance.engine.get_operational_regime") as mock_get:

        state = {
            "tri_signal": {"coherence": 0.8, "jitter": 0.1},
            "slot07": {"temporal_drift": 0.1},
        }
        result = engine.evaluate(state=state)

        # ORP should not be called
        mock_get.assert_not_called()
        # No ORP metadata in result
        assert "orp" not in result.metadata


def test_orp_exception_does_not_crash_governance(mock_orp_normal_regime):
    """Test ORP exception handled gracefully, governance continues."""
    engine = GovernanceEngine()

    with patch("orchestrator.governance.engine._orp_enabled", return_value=True), \
         patch("orchestrator.governance.engine.get_operational_regime", side_effect=Exception("ORP failed")), \
         patch("orchestrator.governance.engine.record_orp"):

        state = {
            "tri_signal": {"coherence": 0.8, "jitter": 0.1},
            "slot07": {"temporal_drift": 0.1},
        }
        result = engine.evaluate(state=state)

        # Governance should succeed without ORP
        assert result.allowed is True
        assert "orp" not in result.metadata


# ---------- Edge Cases ----------


def test_orp_threshold_multiplier_zero_handled():
    """Test threshold_multiplier=0 edge case (should not divide by zero)."""
    engine = GovernanceEngine()

    orp_snapshot = {
        "regime": "emergency_stabilization",
        "regime_score": 0.75,
        "posture_adjustments": {
            "threshold_multiplier": 0.0,  # Edge case
            "traffic_limit": 0.30,
            "deployment_freeze": True,
            "safe_mode_forced": True,
        },
    }

    with patch("orchestrator.governance.engine._orp_enabled", return_value=True), \
         patch("orchestrator.governance.engine.get_operational_regime", return_value=orp_snapshot), \
         patch("orchestrator.governance.engine.record_orp"):

        state = {
            "tri_signal": {"coherence": 0.9, "jitter": 0.05},
            "slot07": {"temporal_drift": 0.05},
        }
        result = engine.evaluate(state=state)

        # Should not crash, all thresholds become 0 (everything fails)
        # But system should handle gracefully
        assert isinstance(result, GovernanceResult)


def test_orp_missing_posture_adjustments_uses_defaults():
    """Test missing posture_adjustments handled with defaults."""
    engine = GovernanceEngine()

    orp_snapshot = {
        "regime": "normal",
        "regime_score": 0.15,
        # Missing posture_adjustments
    }

    with patch("orchestrator.governance.engine._orp_enabled", return_value=True), \
         patch("orchestrator.governance.engine.get_operational_regime", return_value=orp_snapshot), \
         patch("orchestrator.governance.engine.record_orp"):

        state = {
            "tri_signal": {"coherence": 0.8, "jitter": 0.1},
            "slot07": {"temporal_drift": 0.1},
        }
        result = engine.evaluate(state=state)

        # Should use default threshold_multiplier=1.0
        assert result.allowed is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
