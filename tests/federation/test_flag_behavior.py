"""Feature-flag behaviour for federation router."""

from __future__ import annotations

import pytest
from fastapi import FastAPI

from nova.federation import federation_server


@pytest.mark.health
def test_router_disabled_when_flag_unset(monkeypatch):
    monkeypatch.delenv("FEDERATION_ENABLED", raising=False)
    monkeypatch.delenv("NOVA_FEDERATION_REGISTRY", raising=False)
    assert federation_server.build_router() is None


@pytest.mark.health
def test_router_enabled_with_flag(enable_federation, make_registry, client_factory):  # pylint: disable=unused-argument
    client = client_factory()
    res = client.get("/federation/health")
    assert res.status_code == 200
    assert "status" in res.json()
