"""Tests for Operational Regime Policy (ORP) - Phase 11

Tests cover:
- Core regime score calculation with weighted signals and CSI inversion
- Regime classification boundary conditions
- Posture adjustments per regime
- Regime transitions with hysteresis and minimum duration
- Global engine singleton behavior
- Prometheus metrics recording
- Integration scenarios (escalation, recovery, oscillation prevention)
"""

import pytest
from datetime import datetime, timezone, timedelta
from src.nova.continuity.operational_regime import (
    OperationalRegimePolicy,
    ContributingFactors,
    PostureAdjustments,
    Regime,
    RegimeSnapshot,
    SIGNAL_WEIGHTS,
    REGIME_THRESHOLDS,
    REGIME_POSTURES,
    get_orp_engine,
    get_operational_regime,
    get_posture_adjustments,
    reset_orp_engine,
)


# ---------- Core Engine Tests ----------


def test_regime_score_calculation_weights():
    """Test regime score uses correct weights and CSI inversion."""
    engine = OperationalRegimePolicy()
    factors = ContributingFactors(
        urf_composite_risk=0.5,
        mse_meta_instability=0.2,
        predictive_collapse_risk=0.3,
        consistency_gap=0.1,
        csi_continuity_index=0.8,  # Will be inverted to 0.2
    )

    score = engine.compute_regime_score(factors)

    # Expected: 0.5*0.30 + 0.2*0.25 + 0.3*0.20 + 0.1*0.15 + 0.2*0.10
    expected = 0.5 * 0.30 + 0.2 * 0.25 + 0.3 * 0.20 + 0.1 * 0.15 + 0.2 * 0.10
    assert abs(score - expected) < 0.001
    assert abs(score - 0.295) < 0.001


def test_regime_score_csi_inversion():
    """Test CSI is inverted (lower CSI = higher risk contribution)."""
    engine = OperationalRegimePolicy()

    # High CSI (0.9) should contribute low risk (0.1)
    factors_high_csi = ContributingFactors(csi_continuity_index=0.9)
    score_high_csi = engine.compute_regime_score(factors_high_csi)

    # Low CSI (0.2) should contribute high risk (0.8)
    factors_low_csi = ContributingFactors(csi_continuity_index=0.2)
    score_low_csi = engine.compute_regime_score(factors_low_csi)

    assert score_low_csi > score_high_csi


def test_regime_score_clamping():
    """Test regime score clamps out-of-range inputs."""
    engine = OperationalRegimePolicy()

    # All signals > 1.0 should be clamped to 1.0
    factors_high = ContributingFactors(
        urf_composite_risk=1.5,
        mse_meta_instability=2.0,
        predictive_collapse_risk=1.2,
        consistency_gap=1.1,
        csi_continuity_index=1.3,  # Clamped to 1.0, inverted to 0.0
    )
    score_high = engine.compute_regime_score(factors_high)
    assert 0.0 <= score_high <= 1.0

    # All signals < 0.0 should be clamped to 0.0
    factors_low = ContributingFactors(
        urf_composite_risk=-0.5,
        mse_meta_instability=-0.3,
        predictive_collapse_risk=-0.1,
        consistency_gap=-0.2,
        csi_continuity_index=-0.1,  # Clamped to 0.0, inverted to 1.0
    )
    score_low = engine.compute_regime_score(factors_low)
    assert 0.0 <= score_low <= 1.0
    # Only CSI contributes (inverted to 1.0 * 0.10 weight)
    assert abs(score_low - 0.10) < 0.001


def test_regime_classification_normal():
    """Test regime classification for normal range [0.0, 0.30)."""
    engine = OperationalRegimePolicy()

    regime = engine.classify_regime(
        regime_score=0.15,
        current_regime=Regime.NORMAL,
        time_in_regime_s=100.0,
    )
    assert regime == Regime.NORMAL


def test_regime_classification_heightened():
    """Test regime classification for heightened range [0.30, 0.50)."""
    engine = OperationalRegimePolicy()

    regime = engine.classify_regime(
        regime_score=0.40,
        current_regime=Regime.NORMAL,
        time_in_regime_s=100.0,
    )
    assert regime == Regime.HEIGHTENED


def test_regime_classification_controlled_degradation():
    """Test regime classification for controlled degradation [0.50, 0.70)."""
    engine = OperationalRegimePolicy()

    regime = engine.classify_regime(
        regime_score=0.60,
        current_regime=Regime.NORMAL,
        time_in_regime_s=100.0,
    )
    assert regime == Regime.CONTROLLED_DEGRADATION


def test_regime_classification_emergency():
    """Test regime classification for emergency [0.70, 0.85)."""
    engine = OperationalRegimePolicy()

    regime = engine.classify_regime(
        regime_score=0.75,
        current_regime=Regime.NORMAL,
        time_in_regime_s=100.0,
    )
    assert regime == Regime.EMERGENCY_STABILIZATION


def test_regime_classification_recovery():
    """Test regime classification for recovery [0.85, 1.0]."""
    engine = OperationalRegimePolicy()

    regime = engine.classify_regime(
        regime_score=0.90,
        current_regime=Regime.NORMAL,
        time_in_regime_s=100.0,
    )
    assert regime == Regime.RECOVERY


def test_regime_classification_boundary_upgrade():
    """Test exact boundary score upgrades to higher regime."""
    engine = OperationalRegimePolicy()

    # Score exactly 0.30 should upgrade to HEIGHTENED
    regime = engine.classify_regime(
        regime_score=0.30,
        current_regime=Regime.NORMAL,
        time_in_regime_s=100.0,
    )
    assert regime == Regime.HEIGHTENED


def test_regime_transition_upgrade_immediate():
    """Test upgrade to higher severity regime occurs immediately."""
    engine = OperationalRegimePolicy()

    # Current: NORMAL, score crosses to HEIGHTENED
    regime = engine.classify_regime(
        regime_score=0.35,
        current_regime=Regime.NORMAL,
        time_in_regime_s=1.0,  # Very short time
    )
    assert regime == Regime.HEIGHTENED


def test_regime_transition_downgrade_hysteresis():
    """Test downgrade requires score to drop below threshold - hysteresis."""
    engine = OperationalRegimePolicy(downgrade_hysteresis=0.05)

    # Current: HEIGHTENED (threshold 0.30-0.50)
    # Score 0.28 is just below 0.30, but not below hysteresis (0.30 - 0.05 = 0.25)
    regime = engine.classify_regime(
        regime_score=0.28,
        current_regime=Regime.HEIGHTENED,
        time_in_regime_s=400.0,  # Enough time
    )
    assert regime == Regime.HEIGHTENED  # No downgrade

    # Score 0.24 is below hysteresis threshold (0.25)
    regime = engine.classify_regime(
        regime_score=0.24,
        current_regime=Regime.HEIGHTENED,
        time_in_regime_s=400.0,
    )
    assert regime == Regime.NORMAL  # Downgrade allowed


def test_regime_transition_downgrade_min_duration():
    """Test downgrade requires minimum time in regime."""
    engine = OperationalRegimePolicy(min_regime_duration_s=300.0)

    # Score well below hysteresis, but insufficient time
    regime = engine.classify_regime(
        regime_score=0.10,
        current_regime=Regime.HEIGHTENED,
        time_in_regime_s=100.0,  # < 300s minimum
    )
    assert regime == Regime.HEIGHTENED  # No downgrade

    # Sufficient time
    regime = engine.classify_regime(
        regime_score=0.10,
        current_regime=Regime.HEIGHTENED,
        time_in_regime_s=350.0,  # >= 300s
    )
    assert regime == Regime.NORMAL  # Downgrade allowed


def test_evaluate_regime_snapshot():
    """Test evaluate() returns complete snapshot."""
    engine = OperationalRegimePolicy()
    factors = ContributingFactors(
        urf_composite_risk=0.40,
        mse_meta_instability=0.10,
        predictive_collapse_risk=0.20,
        consistency_gap=0.05,
        csi_continuity_index=0.90,
    )

    snapshot = engine.evaluate(factors=factors)

    assert isinstance(snapshot, RegimeSnapshot)
    # Score = 0.40*0.30 + 0.10*0.25 + 0.20*0.20 + 0.05*0.15 + 0.10*0.10 = 0.1975 → NORMAL
    assert snapshot.regime == Regime.NORMAL
    assert 0.0 <= snapshot.regime_score <= 1.0
    assert snapshot.contributing_factors == factors
    assert isinstance(snapshot.posture_adjustments, PostureAdjustments)
    assert snapshot.timestamp is not None


def test_evaluate_tracks_transitions():
    """Test evaluate() tracks regime transitions."""
    engine = OperationalRegimePolicy(min_regime_duration_s=0.0)

    # First evaluation: NORMAL
    factors_normal = ContributingFactors(urf_composite_risk=0.1)
    snapshot1 = engine.evaluate(factors=factors_normal)
    assert snapshot1.regime == Regime.NORMAL
    assert snapshot1.transition_from is None

    # Second evaluation: upgrade to HEIGHTENED (score = 1.0*0.30 + 1.0*0.10 = 0.40 → HEIGHTENED)
    factors_high = ContributingFactors(
        urf_composite_risk=1.0,
        csi_continuity_index=0.0  # Inverted to 1.0
    )
    snapshot2 = engine.evaluate(factors=factors_high)
    assert snapshot2.regime == Regime.HEIGHTENED
    assert snapshot2.transition_from == Regime.NORMAL


def test_reset_engine():
    """Test reset() returns engine to NORMAL."""
    engine = OperationalRegimePolicy()
    # Score = 0.8*0.30 + 0.95*0.25 + 0.0*0.20 + 0.0*0.15 + 1.0*0.10 = 0.5775 → CONTROLLED_DEGRADATION
    factors_high = ContributingFactors(
        urf_composite_risk=0.8,
        mse_meta_instability=0.95,
        csi_continuity_index=0.0
    )
    engine.evaluate(factors=factors_high)
    assert engine.get_current_regime() != Regime.NORMAL

    engine.reset()
    assert engine.get_current_regime() == Regime.NORMAL
    assert engine.get_last_snapshot() is None


# ---------- Posture Tests ----------


def test_normal_posture():
    """Test NORMAL regime posture values."""
    posture = REGIME_POSTURES[Regime.NORMAL]
    assert posture.threshold_multiplier == 1.0
    assert posture.traffic_limit == 1.0
    assert posture.deployment_freeze is False
    assert posture.safe_mode_forced is False
    assert posture.monitoring_interval_s == 60


def test_heightened_posture():
    """Test HEIGHTENED regime posture values."""
    posture = REGIME_POSTURES[Regime.HEIGHTENED]
    assert posture.threshold_multiplier == 0.85
    assert posture.traffic_limit == 0.90
    assert posture.deployment_freeze is False
    assert posture.safe_mode_forced is False
    assert posture.monitoring_interval_s == 30


def test_controlled_degradation_posture():
    """Test CONTROLLED_DEGRADATION regime posture values."""
    posture = REGIME_POSTURES[Regime.CONTROLLED_DEGRADATION]
    assert posture.threshold_multiplier == 0.70
    assert posture.traffic_limit == 0.60
    assert posture.deployment_freeze is True
    assert posture.safe_mode_forced is False
    assert posture.monitoring_interval_s == 20


def test_emergency_stabilization_posture():
    """Test EMERGENCY_STABILIZATION regime posture values."""
    posture = REGIME_POSTURES[Regime.EMERGENCY_STABILIZATION]
    assert posture.threshold_multiplier == 0.60
    assert posture.traffic_limit == 0.30
    assert posture.deployment_freeze is True
    assert posture.safe_mode_forced is True
    assert posture.monitoring_interval_s == 10


def test_recovery_posture():
    """Test RECOVERY regime posture values."""
    posture = REGIME_POSTURES[Regime.RECOVERY]
    assert posture.threshold_multiplier == 0.50
    assert posture.traffic_limit == 0.10
    assert posture.deployment_freeze is True
    assert posture.safe_mode_forced is True
    assert posture.monitoring_interval_s == 10


# ---------- Global Engine Tests ----------


def test_global_engine_singleton():
    """Test get_orp_engine() returns same instance."""
    reset_orp_engine()
    engine1 = get_orp_engine()
    engine2 = get_orp_engine()
    assert engine1 is engine2


def test_get_operational_regime_dict():
    """Test get_operational_regime() returns serializable dict."""
    reset_orp_engine()
    factors = ContributingFactors(urf_composite_risk=0.5)
    result = get_operational_regime(factors=factors)

    assert isinstance(result, dict)
    assert "regime" in result
    assert "regime_score" in result
    assert "contributing_factors" in result
    assert "posture_adjustments" in result
    assert "timestamp" in result


def test_get_posture_adjustments_no_evaluation():
    """Test get_posture_adjustments() returns NORMAL when no evaluation."""
    reset_orp_engine()
    posture = get_posture_adjustments()

    assert posture["threshold_multiplier"] == 1.0
    assert posture["traffic_limit"] == 1.0
    assert posture["deployment_freeze"] is False


def test_get_posture_adjustments_after_evaluation():
    """Test get_posture_adjustments() returns current posture."""
    reset_orp_engine()
    # Score = 0.7*0.30 + 0.8*0.25 + 0.0*0.20 + 0.0*0.15 + 1.0*0.10 = 0.51 → CONTROLLED_DEGRADATION
    factors = ContributingFactors(
        urf_composite_risk=0.7,
        mse_meta_instability=0.8,
        csi_continuity_index=0.0
    )
    get_operational_regime(factors=factors)

    posture = get_posture_adjustments()
    # Should be CONTROLLED_DEGRADATION or higher
    assert posture["threshold_multiplier"] < 1.0
    assert posture["deployment_freeze"] is True


# ---------- Prometheus Metrics Tests ----------


def test_record_orp_metrics_normal():
    """Test record_orp() with NORMAL regime."""
    from orchestrator.prometheus_metrics import record_orp, orp_regime_gauge

    snapshot = {
        "regime": "normal",
        "regime_score": 0.15,
        "posture_adjustments": {
            "threshold_multiplier": 1.0,
            "traffic_limit": 1.0,
            "deployment_freeze": False,
            "safe_mode_forced": False,
        },
        "transition_from": None,
    }
    record_orp(snapshot)

    # Verify gauge values
    assert orp_regime_gauge._value.get() == 0.0  # normal=0


def test_record_orp_metrics_heightened():
    """Test record_orp() with HEIGHTENED regime."""
    from orchestrator.prometheus_metrics import (
        record_orp,
        orp_regime_gauge,
        orp_regime_score_gauge,
        orp_threshold_multiplier_gauge,
    )

    snapshot = {
        "regime": "heightened",
        "regime_score": 0.38,
        "posture_adjustments": {
            "threshold_multiplier": 0.85,
            "traffic_limit": 0.90,
            "deployment_freeze": False,
            "safe_mode_forced": False,
        },
    }
    record_orp(snapshot)

    assert orp_regime_gauge._value.get() == 1.0  # heightened=1
    assert abs(orp_regime_score_gauge._value.get() - 0.38) < 0.01
    assert abs(orp_threshold_multiplier_gauge._value.get() - 0.85) < 0.01


def test_record_orp_metrics_emergency():
    """Test record_orp() with EMERGENCY regime and forced flags."""
    from orchestrator.prometheus_metrics import (
        record_orp,
        orp_regime_gauge,
        orp_deployment_freeze_gauge,
        orp_safe_mode_forced_gauge,
    )

    snapshot = {
        "regime": "emergency_stabilization",
        "regime_score": 0.76,
        "posture_adjustments": {
            "threshold_multiplier": 0.60,
            "traffic_limit": 0.30,
            "deployment_freeze": True,
            "safe_mode_forced": True,
        },
    }
    record_orp(snapshot)

    assert orp_regime_gauge._value.get() == 3.0  # emergency=3
    assert orp_deployment_freeze_gauge._value.get() == 1.0
    assert orp_safe_mode_forced_gauge._value.get() == 1.0


def test_record_orp_transition_counter():
    """Test record_orp() increments transition counter."""
    from orchestrator.prometheus_metrics import record_orp, orp_regime_transitions_counter

    # Get initial count
    initial = orp_regime_transitions_counter.labels(
        from_regime="normal", to_regime="heightened"
    )._value.get()

    snapshot = {
        "regime": "heightened",
        "regime_score": 0.35,
        "posture_adjustments": {},
        "transition_from": "normal",
    }
    record_orp(snapshot)

    # Check counter incremented
    final = orp_regime_transitions_counter.labels(
        from_regime="normal", to_regime="heightened"
    )._value.get()
    assert final == initial + 1


# ---------- Integration Scenarios ----------


def test_scenario_normal_to_recovery_escalation():
    """Test full escalation from NORMAL to RECOVERY."""
    reset_orp_engine()
    engine = get_orp_engine()

    # Start NORMAL (score = 0.1*0.30 = 0.03)
    factors1 = ContributingFactors(urf_composite_risk=0.1)
    snap1 = engine.evaluate(factors=factors1)
    assert snap1.regime == Regime.NORMAL

    # Escalate to HEIGHTENED (score = 0.6*0.30 + 0.8*0.25 = 0.38)
    factors2 = ContributingFactors(urf_composite_risk=0.6, mse_meta_instability=0.8)
    snap2 = engine.evaluate(factors=factors2)
    assert snap2.regime == Regime.HEIGHTENED
    assert snap2.transition_from == Regime.NORMAL

    # Escalate to CONTROLLED_DEGRADATION (score = 0.8*0.30 + 0.7*0.25 + 0.5*0.20 = 0.515)
    factors3 = ContributingFactors(
        urf_composite_risk=0.8,
        mse_meta_instability=0.7,
        predictive_collapse_risk=0.5
    )
    snap3 = engine.evaluate(factors=factors3)
    assert snap3.regime == Regime.CONTROLLED_DEGRADATION

    # Escalate to EMERGENCY (score = 0.9*0.30 + 0.8*0.25 + 0.9*0.20 + 0.7*0.15 = 0.755)
    factors4 = ContributingFactors(
        urf_composite_risk=0.9,
        mse_meta_instability=0.8,
        predictive_collapse_risk=0.9,
        consistency_gap=0.7
    )
    snap4 = engine.evaluate(factors=factors4)
    assert snap4.regime == Regime.EMERGENCY_STABILIZATION

    # Escalate to RECOVERY (score = 0.95*0.30 + 0.95*0.25 + 0.95*0.20 + 0.9*0.15 + 1.0*0.10 = 0.9475)
    factors5 = ContributingFactors(
        urf_composite_risk=0.95,
        mse_meta_instability=0.95,
        predictive_collapse_risk=0.95,
        consistency_gap=0.9,
        csi_continuity_index=0.0
    )
    snap5 = engine.evaluate(factors=factors5)
    assert snap5.regime == Regime.RECOVERY


def test_scenario_recovery_to_normal_gradual_downgrade():
    """Test gradual recovery from RECOVERY to NORMAL with hysteresis."""
    reset_orp_engine()
    engine = OperationalRegimePolicy(downgrade_hysteresis=0.05, min_regime_duration_s=0.0)

    # Start RECOVERY (score = 0.95*0.30 + 0.95*0.25 + 0.95*0.20 + 0.9*0.15 + 1.0*0.10 = 0.9475)
    factors1 = ContributingFactors(
        urf_composite_risk=0.95,
        mse_meta_instability=0.95,
        predictive_collapse_risk=0.95,
        consistency_gap=0.9,
        csi_continuity_index=0.0
    )
    snap1 = engine.evaluate(factors=factors1)
    assert snap1.regime == Regime.RECOVERY

    # Drop to EMERGENCY range (score must be < 0.80 to escape hysteresis: 0.78*0.30 + 0.75*0.25 + 0.70*0.20 + 0.65*0.15 + 1.0*0.10 = 0.7215)
    factors2 = ContributingFactors(
        urf_composite_risk=0.78,
        mse_meta_instability=0.75,
        predictive_collapse_risk=0.70,
        consistency_gap=0.65,
        csi_continuity_index=0.0
    )
    snap2 = engine.evaluate(factors=factors2)
    assert snap2.regime == Regime.EMERGENCY_STABILIZATION

    # Drop to CONTROLLED range (score = 0.7*0.30 + 0.6*0.25 + 0.5*0.20 + 0.4*0.15 + 1.0*0.10 = 0.52)
    factors3 = ContributingFactors(
        urf_composite_risk=0.7,
        mse_meta_instability=0.6,
        predictive_collapse_risk=0.5,
        consistency_gap=0.4,
        csi_continuity_index=0.0
    )
    snap3 = engine.evaluate(factors=factors3)
    assert snap3.regime == Regime.CONTROLLED_DEGRADATION

    # Drop to HEIGHTENED range (score = 0.5*0.30 + 0.4*0.25 + 0.3*0.20 + 0.2*0.15 + 1.0*0.10 = 0.36)
    factors4 = ContributingFactors(
        urf_composite_risk=0.5,
        mse_meta_instability=0.4,
        predictive_collapse_risk=0.3,
        consistency_gap=0.2,
        csi_continuity_index=0.0
    )
    snap4 = engine.evaluate(factors=factors4)
    assert snap4.regime == Regime.HEIGHTENED

    # Drop to NORMAL range (score = 0.2*0.30 + 0.1*0.25 + 0.05*0.20 + 0.0*0.15 + 1.0*0.10 = 0.195)
    factors5 = ContributingFactors(
        urf_composite_risk=0.2,
        mse_meta_instability=0.1,
        predictive_collapse_risk=0.05,
        consistency_gap=0.0,
        csi_continuity_index=0.0
    )
    snap5 = engine.evaluate(factors=factors5)
    assert snap5.regime == Regime.NORMAL


def test_scenario_oscillation_prevention():
    """Test hysteresis prevents rapid oscillation at boundary."""
    reset_orp_engine()
    engine = OperationalRegimePolicy(downgrade_hysteresis=0.05, min_regime_duration_s=300.0)

    # Enter HEIGHTENED (score = 0.6*0.30 + 0.8*0.25 = 0.38)
    factors1 = ContributingFactors(urf_composite_risk=0.6, mse_meta_instability=0.8)
    snap1 = engine.evaluate(factors=factors1)
    assert snap1.regime == Regime.HEIGHTENED

    # Score drops to 0.28 (just below 0.30 threshold, but not below hysteresis 0.25)
    # Score = 0.5*0.30 + 0.5*0.25 + 0.0*0.20 + 0.0*0.15 + 0.3*0.10 = 0.305 (stays HEIGHTENED)
    factors2 = ContributingFactors(urf_composite_risk=0.5, mse_meta_instability=0.5, csi_continuity_index=0.7)
    snap2 = engine.evaluate(factors=factors2)
    assert snap2.regime == Regime.HEIGHTENED

    # Even if time passes, score 0.305 not below hysteresis (0.25)
    engine._current_regime_start = datetime.now(timezone.utc) - timedelta(seconds=400)
    snap3 = engine.evaluate(factors=factors2)
    assert snap3.regime == Regime.HEIGHTENED

    # Score drops to 0.23 (below hysteresis 0.25) and enough time passed
    # Score = 0.3*0.30 + 0.3*0.25 + 0.0*0.20 + 0.0*0.15 + 0.7*0.10 = 0.235
    factors4 = ContributingFactors(urf_composite_risk=0.3, mse_meta_instability=0.3, csi_continuity_index=0.3)
    snap4 = engine.evaluate(factors=factors4)
    assert snap4.regime == Regime.NORMAL  # Now downgrade allowed


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
