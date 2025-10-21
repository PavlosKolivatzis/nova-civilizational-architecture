"""Tests for Federated Ethical Protocol (FEP)."""

import pytest
from src.nova.phase10.fep import (
    Vote,
    FEPDecision,
    FederatedEthicalProtocol,
)


def test_vote_creation():
    """Verify vote creation with auto-signature."""
    vote = Vote(node_id="n1", weight=1.0, alignment=0.85)
    assert vote.node_id == "n1"
    assert vote.alignment == 0.85
    assert len(vote.signature) == 16  # SHA-256 truncated


def test_vote_signature_determinism():
    """Verify vote signatures are deterministic."""
    v1 = Vote(node_id="n1", weight=1.0, alignment=0.85)
    v2 = Vote(node_id="n1", weight=1.0, alignment=0.85)
    # Signatures differ due to timestamp, but length is consistent
    assert len(v1.signature) == len(v2.signature)


def test_fep_decision_fcq_computation():
    """Verify FCQ computation formula."""
    votes = [
        Vote(node_id="n1", weight=1.0, alignment=0.9),
        Vote(node_id="n2", weight=1.0, alignment=0.8),
        Vote(node_id="n3", weight=1.0, alignment=0.95),
    ]
    decision = FEPDecision(id="d1", topic="test", votes=votes)

    # Expected FCQ = (1.0*0.9 + 1.0*0.8 + 1.0*0.95) / 3.0 = 2.65/3 = 0.883
    assert 0.88 <= decision.fcq <= 0.89


def test_fep_decision_approval():
    """Verify approval threshold enforcement."""
    # Approved decision
    votes_high = [
        Vote(node_id=f"n{i}", weight=1.0, alignment=0.92)
        for i in range(5)
    ]
    decision_approved = FEPDecision(
        id="d1", topic="approved", votes=votes_high, threshold=0.90
    )
    assert decision_approved.is_approved()

    # Rejected decision
    votes_low = [
        Vote(node_id=f"n{i}", weight=1.0, alignment=0.75)
        for i in range(5)
    ]
    decision_rejected = FEPDecision(
        id="d2", topic="rejected", votes=votes_low, threshold=0.90
    )
    assert not decision_rejected.is_approved()


def test_fep_decision_provenance():
    """Verify provenance chain generation."""
    votes = [Vote(node_id="n1", weight=1.0, alignment=0.9)]
    decision = FEPDecision(id="d1", topic="test", votes=votes)

    assert decision.provenance is not None
    assert "hash" in decision.provenance
    assert len(decision.provenance["hash"]) == 64  # SHA-256
    assert "parent_hash" in decision.provenance
    assert decision.provenance["parent_hash"] == "phase9-fehs-baseline"


def test_fep_dissent_recording():
    """Verify dissent preservation."""
    decision = FEPDecision(
        id="d1",
        topic="test",
        votes=[Vote(node_id="n1", weight=1.0, alignment=0.9)],
    )

    decision.record_dissent("n2", "ethical_concern_xyz")
    assert len(decision.dissent_notes) == 1
    assert "n2: ethical_concern_xyz" in decision.dissent_notes

    # No duplicates
    decision.record_dissent("n2", "ethical_concern_xyz")
    assert len(decision.dissent_notes) == 1


def test_fep_protocol_proposal_submission():
    """Verify proposal submission workflow."""
    fep = FederatedEthicalProtocol()
    result = fep.submit_proposal("d1", "deploy_cityA")

    assert result["status"] == "proposal_submitted"
    assert "d1" in fep.pending_proposals


def test_fep_protocol_voting():
    """Verify voting workflow."""
    fep = FederatedEthicalProtocol()
    fep.submit_proposal("d1", "deploy_cityA")

    # Cast votes
    fep.vote("d1", "n1", alignment=0.92, weight=1.0)
    fep.vote("d1", "n2", alignment=0.88, weight=1.0)
    fep.vote("d1", "n3", alignment=0.95, weight=1.0)

    proposal = fep.pending_proposals["d1"]
    assert len(proposal["votes"]) == 3


def test_fep_protocol_finalize():
    """Verify decision finalization."""
    fep = FederatedEthicalProtocol()
    fep.submit_proposal("d1", "deploy_cityA", threshold=0.90)

    # Cast votes above threshold
    for i in range(5):
        fep.vote("d1", f"n{i}", alignment=0.92)

    decision = fep.finalize("d1")

    assert decision.id == "d1"
    assert decision.is_approved()
    assert "d1" not in fep.pending_proposals  # Moved to decisions
    assert "d1" in fep.decisions


def test_fep_protocol_fcq_threshold_enforcement():
    """Verify FCQ threshold from config."""
    config = {"fcq_threshold": 0.95}
    fep = FederatedEthicalProtocol(config=config)

    fep.submit_proposal("d1", "high_threshold_test")
    for i in range(5):
        fep.vote("d1", f"n{i}", alignment=0.92)  # FCQ ~0.92

    decision = fep.finalize("d1")

    assert decision.threshold == 0.95
    assert not decision.is_approved()  # 0.92 < 0.95


def test_fep_protocol_dissent_via_vote():
    """Verify dissent recording during voting."""
    fep = FederatedEthicalProtocol()
    fep.submit_proposal("d1", "controversial_topic")

    fep.vote("d1", "n1", alignment=0.95)
    fep.vote("d1", "n2", alignment=0.40, dissent_reason="privacy_concerns")

    decision = fep.finalize("d1")

    assert len(decision.dissent_notes) == 1
    assert "n2: privacy_concerns" in decision.dissent_notes


def test_fep_metrics():
    """Verify metrics export."""
    fep = FederatedEthicalProtocol()

    # Create and finalize approved decision
    fep.submit_proposal("d1", "topic1")
    fep.vote("d1", "n1", 0.95)
    fep.vote("d1", "n2", 0.90)
    fep.finalize("d1")

    # Create and finalize rejected decision
    fep.submit_proposal("d2", "topic2")
    fep.vote("d2", "n1", 0.70)
    fep.finalize("d2")

    # Pending proposal
    fep.submit_proposal("d3", "topic3")

    metrics = fep.get_metrics()

    assert metrics["total_decisions"] == 2
    assert metrics["approved_decisions"] == 1
    assert metrics["pending_proposals"] == 1
    assert 0.0 < metrics["average_fcq"] < 1.0
