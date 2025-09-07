import pytest

from app import app


@pytest.fixture
def client():
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client


def test_validate_architecture_requires_auth(client):
    response = client.post("/api/validate_architecture", json={})
    assert response.status_code == 401


def test_validate_architecture(client, auth_header):
    response = client.post("/api/validate_architecture", json={}, headers=auth_header)
    assert response.status_code == 400
    assert response.get_json() == {
        "client": "test",
        "validation": "failed",
        "error": "Missing required fields",
    }

    payload = {
        "analysis": {
            "slot": "model_update",
            "expected_effectiveness": {
                "conflict_risk": "high",
                "stability_index": 38.1,
                "escalation_risk": "med",
                "side_effects": "low",
            },
            "actual_effectiveness": {
                "conflict_risk": "",
                "stability_index": None,
                "escalation_risk": "",
                "side_effects": "",
            },
        },
        "cultural_alignment": {
            "region": "DE",
            "lang": "german",
            "lang_orientation": "svo",
        },
        "psychology_matrix": {
            "type": "collectivism",
            "dominant_trait": "stoic",
        },
        "philosophy_enforcement": {
            "primary": "humanism",
            "secondary": "stoicism",
            "tertiary": "",
        },
        "diversity_model": {
            "dimension": "linguistic",
            "status": "supported",
        },
    }

    response = client.post("/api/validate_architecture", json=payload, headers=auth_header)
    assert response.status_code == 200
    assert response.get_json() == payload


def test_validate_architecture_rejects_non_mapping_payload(client, auth_header):
    """The endpoint should gracefully handle JSON types other than objects."""

    response = client.post("/api/validate_architecture", json=[1, 2, 3], headers=auth_header)
    assert response.status_code == 400
    assert response.get_json() == {
        "client": "test",
        "validation": "failed",
        "error": "Missing required fields",
    }
