"""Sentinel test for provenance presence in health endpoints."""

import pytest
from fastapi.testclient import TestClient
from nova.orchestrator.app import app

pytestmark = pytest.mark.health

def _get(client, path="/health"):
    """Helper to get health endpoint and validate response."""
    r = client.get(path)
    r.raise_for_status()
    return r.json()

def test_slot3_and_slot6_provenance_present():
    """Ensure Slot 3 and Slot 6 always provide provenance fields.

    This is a sentinel test that fails fast if provenance disappears
    from the health endpoint. It validates the exact structure expected
    by CI workflows.
    """
    c = TestClient(app)
    data = _get(c)

    # Validate overall structure
    assert "slot_self_checks" in data, "/health missing slot_self_checks"
    slot_checks = data["slot_self_checks"]

    # Validate Slot 3 provenance
    assert "slot03_emotional_matrix" in slot_checks, "Slot 3 missing from health checks"
    slot3 = slot_checks["slot03_emotional_matrix"]
    assert "schema_id" in slot3, "Slot 3 missing schema_id"
    assert "schema_version" in slot3, "Slot 3 missing schema_version"
    assert isinstance(slot3["schema_id"], str), "Slot 3 schema_id not string"
    assert isinstance(slot3["schema_version"], str), "Slot 3 schema_version not string"

    # Validate Slot 6 provenance
    assert "slot06_cultural_synthesis" in slot_checks, "Slot 6 missing from health checks"
    slot6 = slot_checks["slot06_cultural_synthesis"]
    assert "schema_id" in slot6, "Slot 6 missing schema_id"
    assert "schema_version" in slot6, "Slot 6 missing schema_version"
    assert isinstance(slot6["schema_id"], str), "Slot 6 schema_id not string"
    assert isinstance(slot6["schema_version"], str), "Slot 6 schema_version not string"

def test_provenance_schema_ids_valid():
    """Validate schema IDs point to expected contract files."""
    c = TestClient(app)
    data = _get(c)

    slot3 = data["slot_self_checks"]["slot03_emotional_matrix"]
    slot6 = data["slot_self_checks"]["slot06_cultural_synthesis"]

    # Check schema IDs contain expected paths/identifiers
    assert "slot3_health_schema" in slot3["schema_id"], f"Invalid Slot 3 schema_id: {slot3['schema_id']}"
    assert "slot6_cultural_profile_schema" in slot6["schema_id"], f"Invalid Slot 6 schema_id: {slot6['schema_id']}"

    # Check version is current
    assert slot3["schema_version"] == "1", f"Unexpected Slot 3 schema version: {slot3['schema_version']}"
    assert slot6["schema_version"] == "1", f"Unexpected Slot 6 schema version: {slot6['schema_version']}"

@pytest.mark.parametrize("serverless", [False, True])
def test_provenance_present_across_modes(serverless, monkeypatch):
    """Ensure provenance works in both normal and serverless modes."""
    if serverless:
        monkeypatch.setenv("VERCEL", "1")
        monkeypatch.setenv("NOVA_HOT_RELOAD", "false")

    c = TestClient(app)
    data = _get(c)

    # Just verify the core provenance is present - don't duplicate full validation
    slot3 = data["slot_self_checks"]["slot03_emotional_matrix"]
    slot6 = data["slot_self_checks"]["slot06_cultural_synthesis"]

    assert {"schema_id", "schema_version"} <= slot3.keys()
    assert {"schema_id", "schema_version"} <= slot6.keys()
