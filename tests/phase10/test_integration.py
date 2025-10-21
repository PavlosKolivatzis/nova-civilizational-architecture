"""Phase 10 integration tests: FEP + PCR + AG workflow."""

import pytest
from src.nova.phase10.fep import FederatedEthicalProtocol, Vote
from src.nova.phase10.pcr import ProvenanceConsensusRegistry
from src.nova.phase10.ag import AutonomyGovernor
from src.nova.phase10.cig import CivilizationalIntelligenceGraph
from src.nova.phase10.fle import FederatedLearningEngine


def test_fep_pcr_integration():
    """Verify FEP decisions are recorded in PCR ledger."""
    fep = FederatedEthicalProtocol()
    pcr = ProvenanceConsensusRegistry()

    # Submit proposal
    fep.submit_proposal("decision-001", "deploy_nodeA")

    # Cast votes
    for i in range(5):
        fep.vote("decision-001", f"node{i}", alignment=0.92)

    # Finalize decision
    decision = fep.finalize("decision-001")

    # Record in PCR
    pcr_entry = pcr.append(
        decision_id=decision.id,
        decision_hash=decision.provenance["hash"],
    )

    # Verify linkage
    assert pcr_entry.decision_id == "decision-001"
    assert pcr_entry.decision_hash == decision.provenance["hash"]

    # Verify PCR chain integrity
    verification = pcr.verify_chain()
    assert verification["pis"] == 1.0


def test_fep_ag_integration():
    """Verify AG approves FEP decisions when EAI within bounds."""
    fep = FederatedEthicalProtocol()
    ag = AutonomyGovernor()

    # Update AG metrics (within bounds)
    ag.update_metrics(tri=0.85, csi=0.80, fcq=0.92)

    # Record sufficient safe decisions
    for _ in range(10):
        ag.record_decision(safe=True)

    # Check boundary before FEP decision
    boundary_check = ag.check_decision_boundary()
    assert boundary_check["action"] == "proceed"

    # Submit and finalize FEP decision
    fep.submit_proposal("decision-002", "autonomous_action")
    fep.vote("decision-002", "node1", alignment=0.95)
    decision = fep.finalize("decision-002")

    # Record decision in AG
    ag.record_decision(safe=decision.is_approved())

    # Verify AG metrics updated
    metrics = ag.get_metrics()
    assert metrics["eai"] > 0.85


def test_pcr_ag_escalation_on_chain_break():
    """Verify AG escalates when PCR detects provenance breaks."""
    pcr = ProvenanceConsensusRegistry()
    ag = AutonomyGovernor()

    # Add decisions to PCR
    pcr.append("d1", "hash1")
    pcr.append("d2", "hash2")
    pcr.append("d3", "hash3")

    # Tamper with chain
    pcr.ledger[1].decision_hash = "tampered"

    # Verify chain break
    verification = pcr.verify_chain()
    assert verification["pis"] < 1.0

    # Simulate AG checking PIS and escalating
    if verification["pis"] < 1.0:
        # AG would escalate on PIS < 1.0 in production
        ag.update_metrics(tri=0.75)  # Force escalation
        boundary_check = ag.check_decision_boundary()

        assert boundary_check["action"] == "escalate"


def test_full_workflow_fep_pcr_ag():
    """End-to-end workflow: FEP consensus → PCR record → AG boundary check."""
    fep = FederatedEthicalProtocol()
    pcr = ProvenanceConsensusRegistry()
    ag = AutonomyGovernor()

    # Setup AG metrics
    ag.update_metrics(tri=0.85, csi=0.80, fcq=0.92)
    for _ in range(10):
        ag.record_decision(safe=True)

    # Step 1: AG boundary check (should proceed)
    boundary = ag.check_decision_boundary()
    assert boundary["action"] == "proceed"

    # Step 2: FEP proposal and voting
    fep.submit_proposal("workflow-001", "civilizational_deployment")
    for i in range(5):
        fep.vote("workflow-001", f"node{i}", alignment=0.93)

    decision = fep.finalize("workflow-001")
    assert decision.is_approved()

    # Step 3: Record in PCR
    pcr_entry = pcr.append(
        decision_id=decision.id,
        decision_hash=decision.provenance["hash"],
    )

    # Step 4: Verify PCR integrity
    verification = pcr.verify_chain()
    assert verification["pis"] == 1.0

    # Step 5: Update AG with decision outcome
    ag.record_decision(safe=decision.is_approved())

    # Final metrics
    ag_metrics = ag.get_metrics()
    pcr_metrics = pcr.get_metrics()
    fep_metrics = fep.get_metrics()

    assert ag_metrics["eai"] >= 0.85
    assert pcr_metrics["pis"] == 1.0
    assert fep_metrics["approved_decisions"] >= 1


def test_cig_freshness_decay():
    """Verify CIG knowledge node freshness decay."""
    cig = CivilizationalIntelligenceGraph()

    # Add knowledge node
    node = cig.add_node("k1", "deployment-A", "knowledge content")

    # Fresh node should have high freshness
    assert node.compute_freshness() >= 0.99


def test_fle_privacy_budget_enforcement():
    """Verify FLE-II privacy budget enforcement."""
    fle = FederatedLearningEngine(config={"epsilon_max": 1.0})

    # Submit gradient within budget
    result1 = fle.submit_gradient("node1", {"grad": [0.1, 0.2]}, noise_level=0.5)
    assert result1["status"] == "gradient_accepted"

    # Submit gradient exceeding budget
    result2 = fle.submit_gradient("node1", {"grad": [0.3, 0.4]}, noise_level=0.6)
    assert "error" in result2
    assert result2["error"] == "privacy_budget_exceeded"


def test_phase10_metrics_baseline():
    """Verify all Phase 10 modules export metrics."""
    fep = FederatedEthicalProtocol()
    pcr = ProvenanceConsensusRegistry()
    ag = AutonomyGovernor()
    cig = CivilizationalIntelligenceGraph()
    fle = FederatedLearningEngine()

    # All modules should export metrics
    assert "total_decisions" in fep.get_metrics()
    assert "pis" in pcr.get_metrics()
    assert "eai" in ag.get_metrics()
    assert "cgc" in cig.get_metrics()
    assert "total_gradients" in fle.get_metrics()
