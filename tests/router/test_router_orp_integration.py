"""Integration tests for ORP in Epistemic Router - Phase 11.2

Tests verify ORP posture adjustments in routing decisions:
- safe_mode_forced forces safe_mode route regardless of score
- traffic_limit rejects requests with 'capacity_limited' route
- threshold_multiplier reduces route scores (tighter scoring)
- ORP metadata recorded in routing decisions
- Flag gating (NOVA_ENABLE_ORP) behavior
"""

import pytest
from unittest.mock import patch, MagicMock
from nova.orchestrator.router.epistemic_router import EpistemicRouter, RouterDecision


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
            "threshold_multiplier": 0.85,  # 15% penalty to scores
            "traffic_limit": 0.90,  # 10% traffic rejected
            "deployment_freeze": False,
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
            "safe_mode_forced": True,  # Forces safe_mode
        },
    }


@pytest.fixture
def router():
    """Create router instance."""
    return EpistemicRouter()


# ---------- Safe Mode Forcing Tests ----------


def test_orp_normal_no_safe_mode_forcing(router, mock_orp_normal_regime):
    """Test normal regime does not force safe_mode."""
    with patch("orchestrator.router.epistemic_router._orp_enabled", return_value=True), \
         patch("orchestrator.router.epistemic_router.get_operational_regime", return_value=mock_orp_normal_regime), \
         patch("orchestrator.router.epistemic_router.record_orp"):

        # High wisdom score should route to creative
        decision = router.decide({"risk": 0.1, "novelty": 0.5})

        assert decision.route != "safe_mode"
        assert decision.metadata["orp"]["regime"] == "normal"


def test_orp_emergency_forces_safe_mode(router, mock_orp_emergency_regime):
    """Test emergency regime forces safe_mode regardless of score."""
    with patch("orchestrator.router.epistemic_router._orp_enabled", return_value=True), \
         patch("orchestrator.router.epistemic_router.get_operational_regime", return_value=mock_orp_emergency_regime), \
         patch("orchestrator.router.epistemic_router.record_orp"):

        # Even with high wisdom, should force safe_mode
        decision = router.decide({"risk": 0.1, "novelty": 0.5})

        assert decision.route == "safe_mode"
        assert decision.final_score == 0.0
        assert "orp_safe_mode_forced" in decision.constraints.reasons
        assert decision.metadata["orp"]["regime"] == "emergency_stabilization"


def test_orp_safe_mode_forced_overrides_policy(router, mock_orp_emergency_regime):
    """Test safe_mode_forced takes precedence over policy route."""
    with patch("orchestrator.router.epistemic_router._orp_enabled", return_value=True), \
         patch("orchestrator.router.epistemic_router.get_operational_regime", return_value=mock_orp_emergency_regime), \
         patch("orchestrator.router.epistemic_router.record_orp"):

        # Policy would normally route to creative
        decision = router.decide({"risk": 0.1, "novelty": 0.5})

        assert decision.route == "safe_mode"
        assert decision.metadata["orp"]["posture"]["safe_mode_forced"] is True


# ---------- Traffic Limiting Tests ----------


def test_orp_traffic_limit_rejects_requests(router, mock_orp_heightened_regime):
    """Test traffic_limit=0.90 rejects ~10% of requests."""
    with patch("orchestrator.router.epistemic_router._orp_enabled", return_value=True), \
         patch("orchestrator.router.epistemic_router.get_operational_regime", return_value=mock_orp_heightened_regime), \
         patch("orchestrator.router.epistemic_router.record_orp"), \
         patch("orchestrator.router.epistemic_router.random.random", return_value=0.95):  # > 0.90 traffic_limit

        decision = router.decide({"risk": 0.1, "novelty": 0.5})

        assert decision.route == "capacity_limited"
        assert decision.final_score == 0.0
        assert "orp_capacity_limit" in decision.constraints.reasons


def test_orp_traffic_limit_allows_requests_within_limit(router, mock_orp_heightened_regime):
    """Test traffic_limit=0.90 allows requests within limit."""
    with patch("orchestrator.router.epistemic_router._orp_enabled", return_value=True), \
         patch("orchestrator.router.epistemic_router.get_operational_regime", return_value=mock_orp_heightened_regime), \
         patch("orchestrator.router.epistemic_router.record_orp"), \
         patch("orchestrator.router.epistemic_router.random.random", return_value=0.50):  # < 0.90 traffic_limit

        decision = router.decide({"risk": 0.1, "novelty": 0.5})

        assert decision.route != "capacity_limited"
        assert decision.metadata["orp"]["regime"] == "heightened"


def test_orp_emergency_traffic_limit_30_percent(router, mock_orp_emergency_regime):
    """Test emergency regime traffic_limit=0.30 rejects 70% of traffic."""
    # First test: request within 30% limit (allowed)
    with patch("orchestrator.router.epistemic_router._orp_enabled", return_value=True), \
         patch("orchestrator.router.epistemic_router.get_operational_regime", return_value=mock_orp_emergency_regime), \
         patch("orchestrator.router.epistemic_router.record_orp"), \
         patch("orchestrator.router.epistemic_router.random.random", return_value=0.10):  # < 0.30

        decision = router.decide({"risk": 0.1, "novelty": 0.5})

        # Should be safe_mode (due to safe_mode_forced), but not capacity_limited
        assert decision.route == "safe_mode"
        assert "orp_capacity_limit" not in decision.constraints.reasons
        assert "orp_safe_mode_forced" in decision.constraints.reasons


    # Second test: request outside 30% limit would reject, but safe_mode_forced takes precedence
    with patch("orchestrator.router.epistemic_router._orp_enabled", return_value=True), \
         patch("orchestrator.router.epistemic_router.get_operational_regime", return_value=mock_orp_emergency_regime), \
         patch("orchestrator.router.epistemic_router.record_orp"), \
         patch("orchestrator.router.epistemic_router.random.random", return_value=0.50):  # > 0.30

        decision = router.decide({"risk": 0.1, "novelty": 0.5})

        # safe_mode_forced takes precedence over traffic limiting
        assert decision.route == "safe_mode"
        assert "orp_safe_mode_forced" in decision.constraints.reasons


# ---------- Threshold Multiplier (Score Penalty) Tests ----------


def test_orp_threshold_multiplier_reduces_scores(router, mock_orp_heightened_regime):
    """Test threshold_multiplier=0.85 applies 15% penalty to route scores."""
    with patch("orchestrator.router.epistemic_router._orp_enabled", return_value=True), \
         patch("orchestrator.router.epistemic_router.get_operational_regime", return_value=mock_orp_heightened_regime), \
         patch("orchestrator.router.epistemic_router.record_orp"), \
         patch("orchestrator.router.epistemic_router.random.random", return_value=0.50):  # Pass traffic limit

        decision = router.decide({"risk": 0.1, "novelty": 0.5})

        # Score should be reduced by threshold_multiplier (0.85)
        # Note: exact score depends on policy calculation, but should be < 1.0
        assert decision.final_score < 1.0
        assert decision.metadata["orp"]["posture"]["threshold_multiplier"] == 0.85


def test_orp_normal_no_score_penalty(router, mock_orp_normal_regime):
    """Test normal regime applies no score penalty (threshold_multiplier=1.0)."""
    with patch("orchestrator.router.epistemic_router._orp_enabled", return_value=True), \
         patch("orchestrator.router.epistemic_router.get_operational_regime", return_value=mock_orp_normal_regime), \
         patch("orchestrator.router.epistemic_router.record_orp"):

        decision = router.decide({"risk": 0.1, "novelty": 0.5})

        # No penalty applied
        assert decision.metadata["orp"]["posture"]["threshold_multiplier"] == 1.0


# ---------- ORP Metadata Recording ----------


def test_orp_metadata_recorded_in_decision(router, mock_orp_heightened_regime):
    """Test ORP metadata included in routing decision."""
    with patch("orchestrator.router.epistemic_router._orp_enabled", return_value=True), \
         patch("orchestrator.router.epistemic_router.get_operational_regime", return_value=mock_orp_heightened_regime), \
         patch("orchestrator.router.epistemic_router.record_orp"), \
         patch("orchestrator.router.epistemic_router.random.random", return_value=0.50):

        decision = router.decide({"risk": 0.1, "novelty": 0.5})

        assert "orp" in decision.metadata
        orp_meta = decision.metadata["orp"]
        assert orp_meta["regime"] == "heightened"
        assert orp_meta["regime_score"] == 0.38
        assert "posture" in orp_meta
        assert orp_meta["posture"]["threshold_multiplier"] == 0.85


def test_orp_metrics_recorded_via_record_orp(router, mock_orp_normal_regime):
    """Test record_orp() called with ORP snapshot."""
    with patch("orchestrator.router.epistemic_router._orp_enabled", return_value=True), \
         patch("orchestrator.router.epistemic_router.get_operational_regime", return_value=mock_orp_normal_regime) as mock_get, \
         patch("orchestrator.router.epistemic_router.record_orp") as mock_record:

        router.decide({"risk": 0.1, "novelty": 0.5})

        # Verify record_orp called
        mock_record.assert_called_once_with(mock_orp_normal_regime)


# ---------- Flag Gating Tests ----------


def test_orp_disabled_no_adjustments(router):
    """Test NOVA_ENABLE_ORP=0 disables all ORP adjustments."""
    with patch("orchestrator.router.epistemic_router._orp_enabled", return_value=False), \
         patch("orchestrator.router.epistemic_router.get_operational_regime") as mock_get:

        decision = router.decide({"risk": 0.1, "novelty": 0.5})

        # ORP should not be called
        mock_get.assert_not_called()
        # No ORP forcing or penalties
        assert decision.route != "capacity_limited"


def test_orp_exception_does_not_crash_router(router, mock_orp_normal_regime):
    """Test ORP exception handled gracefully, routing continues."""
    with patch("orchestrator.router.epistemic_router._orp_enabled", return_value=True), \
         patch("orchestrator.router.epistemic_router.get_operational_regime", side_effect=Exception("ORP failed")), \
         patch("orchestrator.router.epistemic_router.record_orp"):

        decision = router.decide({"risk": 0.1, "novelty": 0.5})

        # Routing should succeed without ORP
        assert isinstance(decision, RouterDecision)


# ---------- Edge Cases ----------


def test_orp_traffic_limit_zero_rejects_all(router):
    """Test traffic_limit=0.0 with safe_mode_forced - safe_mode takes precedence."""
    orp_snapshot = {
        "regime": "recovery",
        "regime_score": 0.91,
        "posture_adjustments": {
            "threshold_multiplier": 0.50,
            "traffic_limit": 0.0,  # Reject all
            "deployment_freeze": True,
            "safe_mode_forced": True,  # Takes precedence
        },
    }

    with patch("orchestrator.router.epistemic_router._orp_enabled", return_value=True), \
         patch("orchestrator.router.epistemic_router.get_operational_regime", return_value=orp_snapshot), \
         patch("orchestrator.router.epistemic_router.record_orp"), \
         patch("orchestrator.router.epistemic_router.random.random", return_value=0.01):  # Any value > 0.0

        decision = router.decide({"risk": 0.1, "novelty": 0.5})

        # safe_mode_forced takes precedence over traffic_limit
        assert decision.route == "safe_mode"
        assert "orp_safe_mode_forced" in decision.constraints.reasons


def test_orp_traffic_limit_one_accepts_all(router):
    """Test traffic_limit=1.0 accepts all requests."""
    orp_snapshot = {
        "regime": "normal",
        "regime_score": 0.15,
        "posture_adjustments": {
            "threshold_multiplier": 1.0,
            "traffic_limit": 1.0,  # Accept all
            "deployment_freeze": False,
            "safe_mode_forced": False,
        },
    }

    with patch("orchestrator.router.epistemic_router._orp_enabled", return_value=True), \
         patch("orchestrator.router.epistemic_router.get_operational_regime", return_value=orp_snapshot), \
         patch("orchestrator.router.epistemic_router.record_orp"), \
         patch("orchestrator.router.epistemic_router.random.random", return_value=0.99):  # Even 0.99 < 1.0

        decision = router.decide({"risk": 0.1, "novelty": 0.5})

        assert decision.route != "capacity_limited"


def test_orp_missing_posture_uses_defaults(router):
    """Test missing posture_adjustments uses safe defaults."""
    orp_snapshot = {
        "regime": "normal",
        "regime_score": 0.15,
        # Missing posture_adjustments
    }

    with patch("orchestrator.router.epistemic_router._orp_enabled", return_value=True), \
         patch("orchestrator.router.epistemic_router.get_operational_regime", return_value=orp_snapshot), \
         patch("orchestrator.router.epistemic_router.record_orp"):

        decision = router.decide({"risk": 0.1, "novelty": 0.5})

        # Should use defaults (no forcing, no limiting)
        assert decision.route != "capacity_limited"
        assert decision.route != "safe_mode" or decision.final_score != 0.0  # Not forced


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
