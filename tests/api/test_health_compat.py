import pytest

pytestmark = pytest.mark.health

try:
    from fastapi.testclient import TestClient
    from nova.orchestrator.app import app
    if app is None:
        raise RuntimeError("FastAPI app unavailable")
except Exception:  # pragma: no cover
    pytest.skip("FastAPI app not available", allow_module_level=True)


def test_health_endpoint_back_compat():
    client = TestClient(app)
    resp = client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"
    assert "slots" in data
    assert "router_thresholds" in data
    assert "circuit_breaker" in data


def test_health_config_endpoint():
    client = TestClient(app)
    resp = client.get("/health/config")
    assert resp.status_code == 200
    data = resp.json()
    assert "hot_reload_enabled" in data
    assert "slots_loaded" in data
    assert isinstance(data.get("slots", []), list)
