"""
Integration tests for Phase 9 URF integration across Governance, Router, and Slot10.

Tests verify:
- Governance blocks on high composite_risk or low alignment_score
- Router applies penalties and routes to safe_mode when URF signals risk
- Slot10 Gatekeeper blocks deployment based on URF thresholds
"""

import os
import pytest
from unittest.mock import Mock, patch


@pytest.fixture(autouse=True)
def enable_urf():
    """Enable URF for all tests in this module."""
    os.environ["NOVA_ENABLE_URF"] = "1"
    yield
    os.environ.pop("NOVA_ENABLE_URF", None)


@pytest.fixture
def mock_urf_stable():
    """URF snapshot: stable, low risk."""
    return {
        "alignment_score": 0.95,
        "risk_gap": 0.05,
        "composite_risk": 0.2,
    }


@pytest.fixture
def mock_urf_high_risk():
    """URF snapshot: high composite risk."""
    return {
        "alignment_score": 0.4,
        "risk_gap": 0.6,
        "composite_risk": 0.9,
    }


@pytest.fixture
def mock_urf_divergent():
    """URF snapshot: divergent signals (low alignment)."""
    return {
        "alignment_score": 0.3,
        "risk_gap": 0.7,
        "composite_risk": 0.5,
    }


# ========== Governance Integration Tests ==========


def test_governance_passes_stable_urf(mock_urf_stable):
    """Test governance allows request when URF is stable."""
    from orchestrator.governance.engine import GovernanceEngine

    with patch("orchestrator.governance.engine.get_unified_risk_field", return_value=mock_urf_stable):
        engine = GovernanceEngine()
        result = engine.evaluate({"user_id": "test-user"})

        assert result.allowed is True
        assert result.metadata["urf"]["composite_risk"] == 0.2
        assert result.metadata["urf"]["alignment_score"] == 0.95


def test_governance_blocks_high_composite_risk(mock_urf_high_risk):
    """Test governance blocks when composite_risk >= 0.7."""
    from orchestrator.governance.engine import GovernanceEngine

    with patch("orchestrator.governance.engine.get_unified_risk_field", return_value=mock_urf_high_risk):
        engine = GovernanceEngine()
        result = engine.evaluate({"user_id": "test-user"})

        assert result.allowed is False
        assert result.reason == "urf_composite_risk_high"
        assert "composite_risk=0.900 >= 0.7" in result.metadata["urf_reason"]


def test_governance_blocks_low_alignment(mock_urf_divergent):
    """Test governance blocks when alignment_score < 0.5."""
    from orchestrator.governance.engine import GovernanceEngine

    with patch("orchestrator.governance.engine.get_unified_risk_field", return_value=mock_urf_divergent):
        engine = GovernanceEngine()
        result = engine.evaluate({"user_id": "test-user"})

        assert result.allowed is False
        assert result.reason == "urf_alignment_low"
        assert "alignment_score=0.300 < 0.5" in result.metadata["urf_reason"]


# ========== Router Integration Tests ==========


def test_router_passes_stable_urf(mock_urf_stable):
    """Test router allows route when URF is stable."""
    from orchestrator.router.epistemic_router import EpistemicRouter
    from orchestrator.router.constraints import ConstraintResult

    with patch("orchestrator.router.epistemic_router.get_unified_risk_field", return_value=mock_urf_stable):
        router = EpistemicRouter()
        request = {"user_id": "test-user", "query": "test"}

        decision = router.decide(request)

        # URF should not block
        assert decision.metadata["urf"]["urf_allowed"] is True
        assert decision.metadata["urf"]["urf_penalty"] == 0.0
        assert decision.metadata["urf"]["composite_risk"] == 0.2


def test_router_blocks_high_composite_risk(mock_urf_high_risk):
    """Test router forces safe_mode when composite_risk >= 0.7."""
    from orchestrator.router.epistemic_router import EpistemicRouter

    with patch("orchestrator.router.epistemic_router.get_unified_risk_field", return_value=mock_urf_high_risk):
        router = EpistemicRouter()
        request = {"user_id": "test-user", "query": "test"}

        decision = router.decide(request)

        assert decision.route == "safe_mode"
        assert decision.metadata["urf"]["urf_allowed"] is False
        assert decision.metadata["urf"]["reason"] == "urf_composite_risk_high"
        assert "urf_composite_risk_high" in decision.constraints.reasons


def test_router_applies_penalty_low_alignment(mock_urf_divergent):
    """Test router applies penalty when alignment_score < 0.5."""
    from orchestrator.router.epistemic_router import EpistemicRouter

    with patch("orchestrator.router.epistemic_router.get_unified_risk_field", return_value=mock_urf_divergent):
        router = EpistemicRouter()
        request = {"user_id": "test-user", "query": "test"}

        decision = router.decide(request)

        # Should apply penalty but not hard block
        assert decision.metadata["urf"]["urf_allowed"] is True
        assert decision.metadata["urf"]["urf_penalty"] > 0.0
        assert decision.metadata["urf"]["reason"] == "urf_alignment_low"


def test_router_penalty_calculation():
    """Test router penalty formula for alignment and gap."""
    from orchestrator.router.epistemic_router import EpistemicRouter

    urf = {
        "alignment_score": 0.3,  # 0.5 - 0.3 = 0.2 → penalty += 0.2 * 0.5 = 0.1
        "risk_gap": 0.6,  # 0.6 - 0.4 = 0.2 → penalty += 0.2 * 0.3 = 0.06
        "composite_risk": 0.5,  # Below 0.7 threshold
    }

    with patch("orchestrator.router.epistemic_router.get_unified_risk_field", return_value=urf):
        router = EpistemicRouter()
        request = {"user_id": "test-user", "query": "test"}

        decision = router.decide(request)

        # Total penalty ≈ 0.1 + 0.06 = 0.16
        assert decision.metadata["urf"]["urf_penalty"] == pytest.approx(0.16, abs=0.01)


# ========== Slot10 Gatekeeper Integration Tests ==========


def test_slot10_passes_stable_urf(mock_urf_stable):
    """Test Slot10 gatekeeper passes when URF is stable."""
    from src.nova.slots.slot10_civilizational_deployment.core.gatekeeper import Gatekeeper

    with patch("src.nova.slots.slot10_civilizational_deployment.core.gatekeeper.get_unified_risk_field", return_value=mock_urf_stable):
        gatekeeper = Gatekeeper()
        result = gatekeeper.evaluate_deploy_gate(
            slot08={"quarantine_active": False, "integrity_score": 0.9, "recent_recoveries": {"success_rate_5m": 0.95}},
            slot04={"safe_mode_active": False, "drift_z": 1.0},
        )

        assert result.passed is True
        assert result.health_snapshot["urf"]["composite_risk"] == 0.2
        assert result.health_snapshot["urf"]["alignment_score"] == 0.95


def test_slot10_blocks_high_composite_risk(mock_urf_high_risk):
    """Test Slot10 blocks deployment when composite_risk >= 0.85."""
    from src.nova.slots.slot10_civilizational_deployment.core.gatekeeper import Gatekeeper

    with patch("src.nova.slots.slot10_civilizational_deployment.core.gatekeeper.get_unified_risk_field", return_value=mock_urf_high_risk):
        gatekeeper = Gatekeeper()
        result = gatekeeper.evaluate_deploy_gate(
            slot08={"quarantine_active": False, "integrity_score": 0.9, "recent_recoveries": {"success_rate_5m": 0.95}},
            slot04={"safe_mode_active": False, "drift_z": 1.0},
        )

        assert result.passed is False
        assert "urf_composite_risk_high" in result.failed_conditions


def test_slot10_blocks_low_alignment(mock_urf_divergent):
    """Test Slot10 blocks deployment when alignment_score < 0.6."""
    from src.nova.slots.slot10_civilizational_deployment.core.gatekeeper import Gatekeeper

    with patch("src.nova.slots.slot10_civilizational_deployment.core.gatekeeper.get_unified_risk_field", return_value=mock_urf_divergent):
        gatekeeper = Gatekeeper()
        result = gatekeeper.evaluate_deploy_gate(
            slot08={"quarantine_active": False, "integrity_score": 0.9, "recent_recoveries": {"success_rate_5m": 0.95}},
            slot04={"safe_mode_active": False, "drift_z": 1.0},
        )

        assert result.passed is False
        assert "urf_alignment_low" in result.failed_conditions


def test_slot10_blocks_high_risk_gap():
    """Test Slot10 blocks deployment when risk_gap > 0.5."""
    from src.nova.slots.slot10_civilizational_deployment.core.gatekeeper import Gatekeeper

    urf = {
        "alignment_score": 0.4,
        "risk_gap": 0.6,  # Exceeds 0.5 threshold
        "composite_risk": 0.6,  # Below 0.85 threshold
    }

    with patch("src.nova.slots.slot10_civilizational_deployment.core.gatekeeper.get_unified_risk_field", return_value=urf):
        gatekeeper = Gatekeeper()
        result = gatekeeper.evaluate_deploy_gate(
            slot08={"quarantine_active": False, "integrity_score": 0.9, "recent_recoveries": {"success_rate_5m": 0.95}},
            slot04={"safe_mode_active": False, "drift_z": 1.0},
        )

        assert result.passed is False
        assert "urf_risk_gap_high" in result.failed_conditions


# ========== End-to-End Integration Test ==========


def test_urf_e2e_cascading_blocks(mock_urf_high_risk):
    """Test all three systems block on same high-risk URF signal."""
    from orchestrator.governance.engine import GovernanceEngine
    from orchestrator.router.epistemic_router import EpistemicRouter
    from src.nova.slots.slot10_civilizational_deployment.core.gatekeeper import Gatekeeper

    with patch("orchestrator.governance.engine.get_unified_risk_field", return_value=mock_urf_high_risk), \
         patch("orchestrator.router.epistemic_router.get_unified_risk_field", return_value=mock_urf_high_risk), \
         patch("src.nova.slots.slot10_civilizational_deployment.core.gatekeeper.get_unified_risk_field", return_value=mock_urf_high_risk):

        # Governance blocks
        gov = GovernanceEngine()
        gov_result = gov.evaluate({"user_id": "test-user"})
        assert gov_result.allowed is False
        assert gov_result.reason == "urf_composite_risk_high"

        # Router blocks
        router = EpistemicRouter()
        router_decision = router.decide({"user_id": "test-user", "query": "test"})
        assert router_decision.route == "safe_mode"
        assert router_decision.metadata["urf"]["urf_allowed"] is False

        # Slot10 blocks
        gatekeeper = Gatekeeper()
        gate_result = gatekeeper.evaluate_deploy_gate(
            slot08={"quarantine_active": False, "integrity_score": 0.9, "recent_recoveries": {"success_rate_5m": 0.95}},
            slot04={"safe_mode_active": False, "drift_z": 1.0},
        )
        assert gate_result.passed is False
        assert "urf_composite_risk_high" in gate_result.failed_conditions
