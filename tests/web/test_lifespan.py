from fastapi.testclient import TestClient
from orchestrator.app import app


def test_health_endpoints_with_lifespan():
    with TestClient(app) as c:
        r = c.get("/health")
        assert r.status_code == 200
        r = c.get("/health/config")
        assert r.status_code == 200
