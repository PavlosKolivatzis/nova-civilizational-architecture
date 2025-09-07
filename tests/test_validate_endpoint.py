import pytest

from app import app


@pytest.fixture
def client():
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client

def test_validate_requires_auth(client):
    response = client.post("/api/validate", json={})
    assert response.status_code == 401


def test_validate_endpoint_rejects_invalid_json(client, auth_header):
    response = client.post(
        "/api/validate", data="not json", content_type="application/json", headers=auth_header
    )
    assert response.status_code == 400
    assert response.get_json() == {"error": "Profile data is required"}


def test_validate_endpoint_rejects_non_mapping(client, auth_header):
    response = client.post("/api/validate", json=[1, 2, 3], headers=auth_header)
    assert response.status_code == 400
    assert response.get_json() == {"error": "Profile data is required"}


def test_validate_endpoint_rejects_non_mapping_profile(client, auth_header):
    response = client.post("/api/validate", json={"profile": []}, headers=auth_header)
    assert response.status_code == 400
    assert response.get_json() == {"error": "Profile data is required"}


def test_validate_endpoint_rejects_non_mapping_payload(client, auth_header):
    response = client.post(
        "/api/validate",
        json={
            "profile": {},
            "institutionType": "academic",
            "payload": [],
        },
        headers=auth_header,
    )
    assert response.status_code == 400
    assert response.get_json() == {"error": "payload must be a JSON object"}
