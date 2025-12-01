"""Regression tests for HTTP security headers."""

import pytest

pytest.importorskip("fastapi")
from fastapi.testclient import TestClient


def test_security_headers_present(monkeypatch):
    """Ensure every response includes the hardened security headers."""
    # Ensure deterministic flag state
    monkeypatch.setenv("NOVA_ENABLE_PROMETHEUS", "0")
    from nova.orchestrator.app import app

    client = TestClient(app)
    response = client.get("/health")

    expected = {
        "X-Content-Type-Options": "nosniff",
        "X-Frame-Options": "DENY",
        "X-XSS-Protection": "1; mode=block",
        "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
    }
    for header, value in expected.items():
        assert response.headers.get(header) == value
