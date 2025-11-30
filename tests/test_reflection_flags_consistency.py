"""Test Nova reflection system flag consistency."""
import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client(monkeypatch):
    """Create test client with reflection flags enabled."""
    # Set minimal flags for fast test execution
    monkeypatch.setenv("NOVA_ENABLE_PROMETHEUS", "1")
    monkeypatch.setenv("NOVA_ANR_ENABLED", "1")
    monkeypatch.setenv("NOVA_ANR_PILOT", "0.0")

    # Import and create app with reflection router
    from nova.orchestrator.app import app
    if app is None:
        pytest.skip("FastAPI not available")
    return TestClient(app)


def test_reflection_flags_consistency(client: TestClient):
    """Test that reflection endpoint captures configured feature flags."""
    response = client.get("/reflect")
    assert response.status_code == 200

    data = response.json()
    flags = data["environment"]["flags"]

    # Core observability flags
    assert flags["NOVA_ENABLE_PROMETHEUS"] == "1"

    # ANR shadow learning flags
    assert flags["NOVA_ANR_ENABLED"] == "1"
    assert flags["NOVA_ANR_PILOT"] == "0.0"


def test_reflection_anr_shadow_mode(client: TestClient):
    """Test that ANR probe shows shadow mode with learning enabled."""
    response = client.get("/reflect")
    assert response.status_code == 200

    data = response.json()
    anr_probe = data["observation"]["anr_probe"]

    # Must be in shadow mode
    assert anr_probe["shadow"] is True

    # Should have entropy and decisiveness metrics
    assert "entropy_bits" in anr_probe
    assert "decisiveness" in anr_probe
    assert isinstance(anr_probe["entropy_bits"], (int, float))
    assert isinstance(anr_probe["decisiveness"], (int, float))


def test_reflection_flow_fabric_status(client: TestClient):
    """Test that flow fabric status is properly reported."""
    response = client.get("/reflect")
    assert response.status_code == 200

    data = response.json()
    flow = data["observation"]["flow_fabric"]

    # Should have initialization and link status
    assert "initialized" in flow
    assert "links" in flow
    assert "status" in flow
    assert isinstance(flow["links"], int)
    assert flow["status"] in ["unknown", "healthy", "error"]
