import pytest

from app import app


@pytest.fixture
def client():
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client


def test_validate_endpoint_rejects_invalid_json(client):
    response = client.post("/api/validate", data="not json", content_type="application/json")
    assert response.status_code == 400
    assert response.get_json() == {"error": "Profile data is required"}


def test_validate_endpoint_rejects_non_mapping(client):
    response = client.post("/api/validate", json=[1, 2, 3])
    assert response.status_code == 400
    assert response.get_json() == {"error": "Profile data is required"}


def test_validate_endpoint_rejects_non_mapping_profile(client):
    response = client.post("/api/validate", json={"profile": []})
    assert response.status_code == 400
    assert response.get_json() == {"error": "Profile data is required"}


def test_validate_endpoint_rejects_non_mapping_payload(client):
    response = client.post(
        "/api/validate",
        json={
            "profile": {},
            "institutionType": "academic",
            "payload": [],
        },
    )
    assert response.status_code == 400
    assert response.get_json() == {"error": "payload must be a JSON object"}
