"""Tests for Nova reflection endpoint contract."""

import pytest
from fastapi.testclient import TestClient


@pytest.mark.parametrize("path", ["/reflect"])
def test_reflect_endpoint(path):
    """Test reflection endpoint contract and response structure."""
    from nova.orchestrator.app import app

    if app is None:
        pytest.skip("FastAPI not available")

    client = TestClient(app)
    response = client.get(path)

    assert response.status_code == 200
    data = response.json()

    # Schema validation
    assert data["schema"] in ("nova.reflection.v1", "nova.reflection.v1.1")
    assert "timestamp" in data
    assert "observation" in data
    assert "claims" in data
    assert "attestations" in data
    assert "meta" in data

    # ANR probe validation
    anr_probe = data["observation"]["anr_probe"]
    assert anr_probe["route"] in ["R1", "R2", "R3", "R4", "R5"]
    assert isinstance(anr_probe["shadow"], bool)
    assert isinstance(anr_probe["confidence"], (int, float))
    # v1.1 uses 'entropy_bits'; fallback to 'entropy' if running v1
    entropy_val = anr_probe.get("entropy_bits", anr_probe.get("entropy"))
    assert isinstance(entropy_val, (int, float))
    assert isinstance(anr_probe["probs"], dict)
    # v1.1: decisiveness present on anr_probe
    if "decisiveness" in anr_probe:
        assert 0.0 <= anr_probe["decisiveness"] <= 1.0
    # v1.1: feature importance present
    if "feature_importance" in anr_probe:
        fi = anr_probe["feature_importance"]
        assert isinstance(fi, dict)
        assert "top_3_influencers" in fi and isinstance(fi["top_3_influencers"], list)

    # Probability distribution validation
    probs = anr_probe["probs"]
    assert isinstance(probs, dict)
    total_prob = sum(probs.values())
    assert 1.0 - 1e-6 <= total_prob <= 1.0 + 1e-6, f"Probabilities don't sum to 1: {total_prob}"

    # Entropy should be reasonable (0 to log2(5) ≈ 2.32 for 5 routes)
    assert 0.0 <= entropy_val <= 2.5

    # Claims validation
    claims = data["claims"]
    for claim_name, claim_value in claims.items():
        assert isinstance(claim_value, (int, float))
        assert 0.0 <= claim_value <= 1.0, f"Claim {claim_name} out of [0,1]: {claim_value}"

    # Health observation validation
    observation = data["observation"]
    assert isinstance(observation["slots_ok"], int)
    assert isinstance(observation["slots_total"], int)
    assert observation["slots_ok"] <= observation["slots_total"]

    # Flow fabric validation
    flow_fabric = observation["flow_fabric"]
    assert isinstance(flow_fabric["initialized"], bool)
    assert isinstance(flow_fabric["links"], int)
    assert flow_fabric["status"] in ["healthy", "degraded", "error", "unknown"]

    # Meta-cognitive validation
    meta = data["meta"]
    assert meta["reflection_capability"] == "architectural_consciousness"
    assert "/" in meta["cognitive_integration"]  # format: "X/Y slots unified"
    assert meta["awakening_status"] in ["emerging", "achieved", "transcendent"]

    # Build info validation
    build = data["build"]
    assert isinstance(build["sha"], str)
    assert isinstance(build["version"], str)

    # v1.1 provenance (optional if running v1)
    if "provenance" in data:
        prov = data["provenance"]
        assert isinstance(prov.get("snapshot_id"), str)
        # decisiveness may be in provenance (your v1.1 spec) or on anr_probe (your impl)
        if "decisiveness" in prov:
            assert 0.0 <= prov["decisiveness"] <= 1.0
        assert isinstance(prov.get("hmac_sha256"), str) and len(prov["hmac_sha256"]) == 64
        if "environment" in data and "flags" in data["environment"]:
            assert isinstance(data["environment"]["flags"], dict)

    # Attestations validation
    attestations = data["attestations"]
    assert attestations["healthkit_schema"] == "1.0"
    assert isinstance(attestations["flow_contracts"], list)


def test_reflect_endpoint_consistency():
    """Test that reflection endpoint returns consistent schema across calls."""
    from nova.orchestrator.app import app

    if app is None:
        pytest.skip("FastAPI not available")

    client = TestClient(app)

    # Make multiple calls
    responses = [client.get("/reflect") for _ in range(3)]

    # All should succeed
    for r in responses:
        assert r.status_code == 200

    data_list = [r.json() for r in responses]

    # Schema should be consistent
    for data in data_list:
        assert data["schema"] in ("nova.reflection.v1", "nova.reflection.v1.1")

    # Structure should be consistent
    first = data_list[0]
    for data in data_list[1:]:
        assert set(data.keys()) == set(first.keys())
        assert set(data["observation"].keys()) == set(first["observation"].keys())
        assert set(data["claims"].keys()) == set(first["claims"].keys())


def test_reflect_endpoint_anr_routing_validity():
    """Test that ANR routing decisions in reflection are valid."""
    from nova.orchestrator.app import app

    if app is None:
        pytest.skip("FastAPI not available")

    client = TestClient(app)
    response = client.get("/reflect")

    assert response.status_code == 200
    data = response.json()

    anr_probe = data["observation"]["anr_probe"]

    # Route must be one of the valid routes
    valid_routes = ["R1", "R2", "R3", "R4", "R5"]
    assert anr_probe["route"] in valid_routes

    # Confidence should match max probability
    max_prob = max(anr_probe["probs"].values())
    assert abs(anr_probe["confidence"] - max_prob) < 1e-6

    # Entropy should be reasonable (0 to log2(5) ≈ 2.32 for 5 routes)
    entropy_val = anr_probe.get("entropy_bits", anr_probe.get("entropy"))
    assert 0.0 <= entropy_val <= 2.5

    # Shadow mode should be True (reflection uses shadow=True)
    assert anr_probe["shadow"] is True


def test_reflect_endpoint_production_readiness_claims():
    """Test production readiness claims are reasonable."""
    from nova.orchestrator.app import app

    if app is None:
        pytest.skip("FastAPI not available")

    client = TestClient(app)
    response = client.get("/reflect")

    assert response.status_code == 200
    data = response.json()

    claims = data["claims"]
    observation = data["observation"]

    # Production readiness should correlate with slot health
    if observation["slots_ok"] >= observation["slots_total"]:
        assert claims["production_ready"] >= 0.9

    # Architectural consciousness should be high if most systems are operational
    if (observation["slots_ok"] >= 10 and
        claims["adaptive_routing_operational"] >= 0.9):
        assert claims["architectural_consciousness"] >= 0.8

    # Observability should be high if we have good slot coverage
    if observation["slots_total"] >= 12:
        assert claims["observability_sufficient"] >= 0.9
