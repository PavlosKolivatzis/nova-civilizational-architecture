import pytest
import jwt
from fastapi.testclient import TestClient

from slots.slot09_distortion_protection.hybrid_api import (
    create_development_config,
    create_hybrid_slot9_api,
    create_fastapi_app,
)
from auth import JWT_SECRET


def _token():
    return jwt.encode({"sub": "test"}, JWT_SECRET, algorithm="HS256")


@pytest.fixture
def client():
    api = create_hybrid_slot9_api(core_detector=None, config=create_development_config())
    app = create_fastapi_app(api)
    if app is None:
        pytest.skip("FastAPI not available")
    return TestClient(app)


def test_health_requires_auth(client):
    resp = client.get("/api/v1/health")
    assert resp.status_code == 401


def test_health_with_token(client):
    resp = client.get("/api/v1/health", headers={"Authorization": f"Bearer {_token()}"})
    assert resp.status_code == 200
    assert "status" in resp.json()
