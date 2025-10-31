"""Shared fixtures for federation tests."""

from __future__ import annotations

import base64
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable
from uuid import uuid4

import pytest
import yaml
from fastapi import FastAPI, Response
from fastapi.testclient import TestClient
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest

from nova.metrics.registry import REGISTRY
from nova.federation.schemas import CheckpointEnvelope
from nova.metrics import federation as federation_metrics


@pytest.fixture(autouse=True)
def reset_federation_metrics():
    federation_metrics.reset_for_tests()
    yield


@pytest.fixture
def make_registry(monkeypatch, tmp_path: Path):
    key_path = tmp_path / "peer.pem"
    key_path.write_text("mock-dilithium2-key", encoding="utf-8")
    registry_path = tmp_path / "peers.yaml"
    registry_path.write_text(
        yaml.safe_dump(
            {
                "federation": {
                    "peers": [
                        {
                            "id": "node-athens",
                            "url": "https://athens.example.net",
                            "pubkey": str(key_path),
                            "enabled": True,
                        }
                    ]
                }
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setenv("NOVA_FEDERATION_REGISTRY", str(registry_path))
    return registry_path


@pytest.fixture
def enable_federation(monkeypatch, make_registry):  # pylint: disable=unused-argument
    monkeypatch.setenv("FEDERATION_ENABLED", "1")
    yield
    monkeypatch.delenv("FEDERATION_ENABLED", raising=False)


@pytest.fixture
def make_envelope() -> Callable[..., CheckpointEnvelope]:
    def _builder(**overrides) -> CheckpointEnvelope:
        payload = dict(
            anchor_id=str(uuid4()),
            merkle_root="a" * 64,
            height=42,
            ts=datetime.now(timezone.utc),
            algo="sha3-256",
            sig_b64=base64.b64encode(b"x" * 600).decode(),
            producer="node-athens",
            version="v1",
        )
        payload.update(overrides)
        return CheckpointEnvelope(**payload)

    return _builder


@pytest.fixture
def client_factory(enable_federation):
    from nova.federation import federation_server

    def _factory() -> TestClient:
        router = federation_server.build_router()
        app = FastAPI()
        if router is not None:
            app.include_router(router)

        @app.get("/metrics")
        def metrics():  # pragma: no cover - exercised via tests
            return Response(content=generate_latest(REGISTRY), media_type=CONTENT_TYPE_LATEST)

        return TestClient(app)

    return _factory
