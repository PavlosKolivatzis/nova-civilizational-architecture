"""Tests for Phase 10 orchestrator endpoints."""

import pytest


@pytest.fixture
def client():
    """FastAPI test client."""
    from fastapi.testclient import TestClient
    from orchestrator.app import app
    return TestClient(app)


def test_fep_proposal_endpoint(client):
    """Test FEP proposal submission."""
    response = client.post(
        "/phase10/fep/proposal",
        json={"decision_id": "test-001", "topic": "test_deployment"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "proposal_submitted"
    assert data["decision_id"] == "test-001"


def test_fep_vote_endpoint(client):
    """Test FEP voting."""
    # Submit proposal first
    client.post(
        "/phase10/fep/proposal",
        json={"decision_id": "test-002", "topic": "test_vote"},
    )

    # Cast vote
    response = client.post(
        "/phase10/fep/vote",
        json={
            "decision_id": "test-002",
            "node_id": "node1",
            "alignment": 0.92,
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "vote_recorded"
    assert data["node_id"] == "node1"


def test_fep_finalize_endpoint(client):
    """Test FEP decision finalization with PCR recording."""
    # Submit proposal
    client.post(
        "/phase10/fep/proposal",
        json={"decision_id": "test-003", "topic": "test_finalize"},
    )

    # Cast votes (above threshold)
    for i in range(5):
        client.post(
            "/phase10/fep/vote",
            json={
                "decision_id": "test-003",
                "node_id": f"node{i}",
                "alignment": 0.93,
            },
        )

    # Finalize
    response = client.post(
        "/phase10/fep/finalize",
        json={"decision_id": "test-003"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "finalized"
    assert data["approved"] is True
    assert data["fcq"] >= 0.90


def test_ag_boundary_enforcement(client):
    """Test AG blocks decisions when TRI violated."""
    from orchestrator.phase10_manager import get_phase10_manager

    # Force TRI violation
    mgr = get_phase10_manager()
    mgr.ag.update_metrics(tri=0.75)  # Below 0.80 threshold

    # Submit proposal
    client.post(
        "/phase10/fep/proposal",
        json={"decision_id": "test-004", "topic": "blocked_decision"},
    )

    # Try to finalize (should be blocked by AG)
    response = client.post(
        "/phase10/fep/finalize",
        json={"decision_id": "test-004"},
    )

    assert response.status_code == 200
    data = response.json()
    assert "error" in data
    assert data["error"] == "ag_blocked"
    assert data["action"] == "escalate"

    # Reset TRI for subsequent tests
    mgr.ag.update_metrics(tri=0.85)


def test_phase10_metrics_endpoint(client):
    """Test Phase 10 metrics export."""
    response = client.get("/phase10/metrics")

    assert response.status_code == 200
    data = response.json()

    # Verify all modules export metrics
    assert "fep" in data
    assert "pcr" in data
    assert "ag" in data
    assert "cig" in data
    assert "fle" in data

    # Spot-check key metrics
    assert "eai" in data["ag"]
    assert "pis" in data["pcr"]
    assert "total_decisions" in data["fep"]


def test_prometheus_metrics_include_phase10(client):
    """Test Prometheus /metrics includes Phase 10 gauges."""
    import os
    os.environ["NOVA_ENABLE_PROMETHEUS"] = "1"

    response = client.get("/metrics")

    assert response.status_code == 200
    body = response.text

    # Verify Phase 10 metrics present
    assert "nova_phase10_eai" in body
    assert "nova_phase10_cgc" in body
    assert "nova_phase10_pis" in body


def test_full_workflow_via_endpoints(client):
    """End-to-end workflow through REST API."""
    # 1. Submit proposal
    client.post(
        "/phase10/fep/proposal",
        json={"decision_id": "workflow-001", "topic": "full_workflow_test"},
    )

    # 2. Cast votes
    for i in range(5):
        client.post(
            "/phase10/fep/vote",
            json={
                "decision_id": "workflow-001",
                "node_id": f"node{i}",
                "alignment": 0.94,
            },
        )

    # 3. Finalize (triggers PCR recording + AG update)
    response = client.post(
        "/phase10/fep/finalize",
        json={"decision_id": "workflow-001"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["approved"] is True

    # 4. Verify metrics updated
    metrics = client.get("/phase10/metrics").json()
    assert metrics["fep"]["approved_decisions"] >= 1
    assert metrics["pcr"]["total_entries"] >= 1
    assert metrics["ag"]["eai"] > 0.0
