"""End-to-end ORP integration scenario tests - Phase 11.2

Tests verify complete ORP behavior across Governance, Router, and Slot10:
- Normal → Emergency escalation scenario
- Recovery → Normal recovery scenario
- Multi-system coordination under ORP regimes
"""

import pytest
from unittest.mock import patch, MagicMock
from nova.orchestrator.governance.engine import GovernanceEngine
from nova.orchestrator.router.epistemic_router import EpistemicRouter
from src.nova.slots.slot10_civilizational_deployment.core.gatekeeper import Gatekeeper
from src.nova.slots.slot10_civilizational_deployment.core.policy import Slot10Policy


@pytest.fixture
def governance_engine():
    return GovernanceEngine()


@pytest.fixture
def router():
    return EpistemicRouter()


@pytest.fixture
def gatekeeper():
    return Gatekeeper(policy=Slot10Policy())


# ---------- Normal → Emergency Escalation Scenario ----------


def test_e2e_normal_regime_all_systems_operational(governance_engine, router, gatekeeper):
    """Test normal regime allows operations across all systems."""
    orp_normal = {
        "regime": "normal",
        "regime_score": 0.15,
        "posture_adjustments": {
            "threshold_multiplier": 1.0,
            "traffic_limit": 1.0,
            "deployment_freeze": False,
            "safe_mode_forced": False,
        },
    }

    with patch("nova.orchestrator.governance.engine._orp_enabled", return_value=True), \
         patch("nova.orchestrator.governance.engine.get_operational_regime", return_value=orp_normal), \
         patch("nova.orchestrator.governance.engine.record_orp"), \
         patch("nova.orchestrator.router.epistemic_router._orp_enabled", return_value=True), \
         patch("nova.orchestrator.router.epistemic_router.get_operational_regime", return_value=orp_normal), \
         patch("nova.orchestrator.router.epistemic_router.record_orp"), \
         patch("src.nova.slots.slot10_civilizational_deployment.core.gatekeeper._orp_enabled", return_value=True), \
         patch("src.nova.slots.slot10_civilizational_deployment.core.gatekeeper.get_operational_regime", return_value=orp_normal), \
         patch("src.nova.slots.slot10_civilizational_deployment.core.gatekeeper.record_orp"):

        # Governance: allows request
        gov_result = governance_engine.evaluate(state={
            "tri_signal": {"coherence": 0.8, "jitter": 0.1},
            "slot07": {"temporal_drift": 0.1},
        })
        assert gov_result.allowed is True

        # Router: routes to creative (not forced to safe_mode)
        router_decision = router.decide({"risk": 0.1, "novelty": 0.5})
        assert router_decision.route != "capacity_limited"
        assert router_decision.route != "safe_mode" or router_decision.final_score > 0.0

        # Slot10: allows deployment
        gate_result = gatekeeper.evaluate_deploy_gate(
            slot08={"quarantine_active": False, "integrity_score": 0.9, "recent_recoveries": {"success_rate_5m": 0.95}},
            slot04={"safe_mode_active": False, "drift_z": 0.5}
        )
        assert gate_result.passed is True


def test_e2e_heightened_regime_tightened_operations(governance_engine, router, gatekeeper):
    """Test heightened regime tightens thresholds but allows operations."""
    orp_heightened = {
        "regime": "heightened",
        "regime_score": 0.38,
        "posture_adjustments": {
            "threshold_multiplier": 0.85,
            "traffic_limit": 0.90,
            "deployment_freeze": False,
            "safe_mode_forced": False,
        },
    }

    with patch("nova.orchestrator.governance.engine._orp_enabled", return_value=True), \
         patch("nova.orchestrator.governance.engine.get_operational_regime", return_value=orp_heightened), \
         patch("nova.orchestrator.governance.engine.record_orp"), \
         patch("nova.orchestrator.router.epistemic_router._orp_enabled", return_value=True), \
         patch("nova.orchestrator.router.epistemic_router.get_operational_regime", return_value=orp_heightened), \
         patch("nova.orchestrator.router.epistemic_router.record_orp"), \
         patch("nova.orchestrator.router.epistemic_router.random.random", return_value=0.50), \
         patch("src.nova.slots.slot10_civilizational_deployment.core.gatekeeper._orp_enabled", return_value=True), \
         patch("src.nova.slots.slot10_civilizational_deployment.core.gatekeeper.get_operational_regime", return_value=orp_heightened), \
         patch("src.nova.slots.slot10_civilizational_deployment.core.gatekeeper.record_orp"):

        # Governance: tightened thresholds, but still allows
        gov_result = governance_engine.evaluate(state={
            "tri_signal": {"coherence": 0.8, "jitter": 0.1},
            "slot07": {"temporal_drift": 0.1},
        })
        assert gov_result.metadata["orp"]["regime"] == "heightened"

        # Router: reduced scores, 10% traffic rejected
        router_decision = router.decide({"risk": 0.1, "novelty": 0.5})
        assert router_decision.metadata["orp"]["regime"] == "heightened"

        # Slot10: still allows deployment
        gate_result = gatekeeper.evaluate_deploy_gate(
            slot08={"quarantine_active": False, "integrity_score": 0.9, "recent_recoveries": {"success_rate_5m": 0.95}},
            slot04={"safe_mode_active": False, "drift_z": 0.5}
        )
        assert gate_result.passed is True


def test_e2e_controlled_degradation_regime_blocks_deployments(governance_engine, router, gatekeeper):
    """Test controlled_degradation regime blocks deployments, limits traffic."""
    orp_controlled = {
        "regime": "controlled_degradation",
        "regime_score": 0.58,
        "posture_adjustments": {
            "threshold_multiplier": 0.70,
            "traffic_limit": 0.60,
            "deployment_freeze": True,
            "safe_mode_forced": False,
        },
    }

    with patch("nova.orchestrator.governance.engine._orp_enabled", return_value=True), \
         patch("nova.orchestrator.governance.engine.get_operational_regime", return_value=orp_controlled), \
         patch("nova.orchestrator.governance.engine.record_orp"), \
         patch("nova.orchestrator.router.epistemic_router._orp_enabled", return_value=True), \
         patch("nova.orchestrator.router.epistemic_router.get_operational_regime", return_value=orp_controlled), \
         patch("nova.orchestrator.router.epistemic_router.record_orp"), \
         patch("nova.orchestrator.router.epistemic_router.random.random", return_value=0.70), \
         patch("src.nova.slots.slot10_civilizational_deployment.core.gatekeeper._orp_enabled", return_value=True), \
         patch("src.nova.slots.slot10_civilizational_deployment.core.gatekeeper.get_operational_regime", return_value=orp_controlled), \
         patch("src.nova.slots.slot10_civilizational_deployment.core.gatekeeper.record_orp"):

        # Governance: very tight thresholds
        gov_result = governance_engine.evaluate(state={
            "tri_signal": {"coherence": 0.8, "jitter": 0.1},
            "slot07": {"temporal_drift": 0.1},
        })
        assert gov_result.metadata["orp"]["regime"] == "controlled_degradation"

        # Router: 40% traffic rejected
        router_decision = router.decide({"risk": 0.1, "novelty": 0.5})
        assert router_decision.route == "capacity_limited"
        assert "orp_capacity_limit" in router_decision.constraints.reasons

        # Slot10: BLOCKS deployment
        gate_result = gatekeeper.evaluate_deploy_gate(
            slot08={"quarantine_active": False, "integrity_score": 0.9, "recent_recoveries": {"success_rate_5m": 0.95}},
            slot04={"safe_mode_active": False, "drift_z": 0.5}
        )
        assert gate_result.passed is False
        assert "orp_deployment_freeze" in gate_result.failed_conditions


def test_e2e_emergency_regime_forces_safe_mode_blocks_all(governance_engine, router, gatekeeper):
    """Test emergency regime forces safe_mode, blocks deployments, rejects most traffic."""
    orp_emergency = {
        "regime": "emergency_stabilization",
        "regime_score": 0.76,
        "posture_adjustments": {
            "threshold_multiplier": 0.60,
            "traffic_limit": 0.30,
            "deployment_freeze": True,
            "safe_mode_forced": True,
        },
    }

    with patch("nova.orchestrator.governance.engine._orp_enabled", return_value=True), \
         patch("nova.orchestrator.governance.engine.get_operational_regime", return_value=orp_emergency), \
         patch("nova.orchestrator.governance.engine.record_orp"), \
         patch("nova.orchestrator.router.epistemic_router._orp_enabled", return_value=True), \
         patch("nova.orchestrator.router.epistemic_router.get_operational_regime", return_value=orp_emergency), \
         patch("nova.orchestrator.router.epistemic_router.record_orp"), \
         patch("nova.orchestrator.router.epistemic_router.random.random", return_value=0.10), \
         patch("src.nova.slots.slot10_civilizational_deployment.core.gatekeeper._orp_enabled", return_value=True), \
         patch("src.nova.slots.slot10_civilizational_deployment.core.gatekeeper.get_operational_regime", return_value=orp_emergency), \
         patch("src.nova.slots.slot10_civilizational_deployment.core.gatekeeper.record_orp"), \
         patch("src.nova.slots.slot10_civilizational_deployment.core.gatekeeper.logger"):

        # Governance: extreme thresholds
        gov_result = governance_engine.evaluate(state={
            "tri_signal": {"coherence": 0.9, "jitter": 0.05},
            "slot07": {"temporal_drift": 0.05},
        })
        assert gov_result.metadata["orp"]["regime"] == "emergency_stabilization"

        # Router: FORCES safe_mode (even with high wisdom)
        router_decision = router.decide({"risk": 0.1, "novelty": 0.5})
        assert router_decision.route == "safe_mode"
        assert "orp_safe_mode_forced" in router_decision.constraints.reasons

        # Slot10: BLOCKS deployment
        gate_result = gatekeeper.evaluate_deploy_gate(
            slot08={"quarantine_active": False, "integrity_score": 0.9, "recent_recoveries": {"success_rate_5m": 0.95}},
            slot04={"safe_mode_active": False, "drift_z": 0.5}
        )
        assert gate_result.passed is False
        assert "orp_deployment_freeze" in gate_result.failed_conditions


# ---------- Recovery → Normal Recovery Scenario ----------


def test_e2e_recovery_regime_requires_manual_approval(governance_engine, router, gatekeeper):
    """Test recovery regime blocks governance without manual_approval."""
    orp_recovery = {
        "regime": "recovery",
        "regime_score": 0.91,
        "posture_adjustments": {
            "threshold_multiplier": 0.50,
            "traffic_limit": 0.10,
            "deployment_freeze": True,
            "safe_mode_forced": True,
        },
    }

    with patch("nova.orchestrator.governance.engine._orp_enabled", return_value=True), \
         patch("nova.orchestrator.governance.engine.get_operational_regime", return_value=orp_recovery), \
         patch("nova.orchestrator.governance.engine.record_orp"):

        # Without manual_approval: BLOCKED
        gov_result = governance_engine.evaluate(state={
            "tri_signal": {"coherence": 0.9, "jitter": 0.05},
            "slot07": {"temporal_drift": 0.05},
        })
        assert gov_result.allowed is False
        assert gov_result.reason == "orp_manual_approval_required"

        # With manual_approval: ALLOWED
        gov_result_approved = governance_engine.evaluate(state={
            "tri_signal": {"coherence": 0.9, "jitter": 0.05},
            "slot07": {"temporal_drift": 0.05},
            "manual_approval": True,
        })
        assert gov_result_approved.allowed is True


def test_e2e_regime_transition_normal_to_recovery_escalation(governance_engine, router, gatekeeper):
    """Test full escalation from normal → recovery affects all systems."""
    regimes = [
        ("normal", 0.15, {"threshold_multiplier": 1.0, "traffic_limit": 1.0, "deployment_freeze": False, "safe_mode_forced": False}),
        ("heightened", 0.38, {"threshold_multiplier": 0.85, "traffic_limit": 0.90, "deployment_freeze": False, "safe_mode_forced": False}),
        ("controlled_degradation", 0.58, {"threshold_multiplier": 0.70, "traffic_limit": 0.60, "deployment_freeze": True, "safe_mode_forced": False}),
        ("emergency_stabilization", 0.76, {"threshold_multiplier": 0.60, "traffic_limit": 0.30, "deployment_freeze": True, "safe_mode_forced": True}),
        ("recovery", 0.91, {"threshold_multiplier": 0.50, "traffic_limit": 0.10, "deployment_freeze": True, "safe_mode_forced": True}),
    ]

    for regime_name, regime_score, posture in regimes:
        orp_snapshot = {
            "regime": regime_name,
            "regime_score": regime_score,
            "posture_adjustments": posture,
        }

        with patch("nova.orchestrator.governance.engine._orp_enabled", return_value=True), \
             patch("nova.orchestrator.governance.engine.get_operational_regime", return_value=orp_snapshot), \
             patch("nova.orchestrator.governance.engine.record_orp"), \
             patch("nova.orchestrator.router.epistemic_router._orp_enabled", return_value=True), \
             patch("nova.orchestrator.router.epistemic_router.get_operational_regime", return_value=orp_snapshot), \
             patch("nova.orchestrator.router.epistemic_router.record_orp"), \
             patch("nova.orchestrator.router.epistemic_router.random.random", return_value=0.05), \
             patch("src.nova.slots.slot10_civilizational_deployment.core.gatekeeper._orp_enabled", return_value=True), \
             patch("src.nova.slots.slot10_civilizational_deployment.core.gatekeeper.get_operational_regime", return_value=orp_snapshot), \
             patch("src.nova.slots.slot10_civilizational_deployment.core.gatekeeper.record_orp"), \
             patch("src.nova.slots.slot10_civilizational_deployment.core.gatekeeper.logger"):

            # Check Governance behavior
            state = {"tri_signal": {"coherence": 0.9, "jitter": 0.05}, "slot07": {"temporal_drift": 0.05}}
            if regime_name == "recovery":
                state["manual_approval"] = True
            gov_result = governance_engine.evaluate(state=state)
            assert gov_result.metadata["orp"]["regime"] == regime_name

            # Check Router behavior
            router_decision = router.decide({"risk": 0.1, "novelty": 0.5})
            if posture["safe_mode_forced"]:
                assert router_decision.route == "safe_mode"

            # Check Slot10 behavior
            gate_result = gatekeeper.evaluate_deploy_gate(
                slot08={"quarantine_active": False, "integrity_score": 0.9, "recent_recoveries": {"success_rate_5m": 0.95}},
                slot04={"safe_mode_active": False, "drift_z": 0.5}
            )
            if posture["deployment_freeze"]:
                assert gate_result.passed is False
                assert "orp_deployment_freeze" in gate_result.failed_conditions


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
