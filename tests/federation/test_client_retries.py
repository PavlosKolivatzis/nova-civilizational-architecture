"""Federation client retry behaviour."""

from __future__ import annotations

import base64
from datetime import datetime, timezone

import httpx
import pytest

from nova.federation.federation_client import FederationClient
from nova.federation.peer_registry import PeerRecord
from nova.federation.schemas import CheckpointEnvelope
from nova.metrics import federation as federation_metrics


def _sample_envelope() -> CheckpointEnvelope:
    return CheckpointEnvelope(
        anchor_id="00000000-0000-0000-0000-000000000000",
        merkle_root="a" * 64,
        height=1,
        ts=datetime.now(timezone.utc),
        sig_b64=base64.b64encode(b"x" * 600).decode(),
        producer="node-athens",
    )


@pytest.mark.health
def test_timeout_retries(monkeypatch):
    peer = PeerRecord(id="node-athens", url="https://athens.example.net", pubkey="keys/a.pem", enabled=True)
    client = FederationClient(timeout_s=0.1, retries=2)
    envelope = _sample_envelope()

    call_count = 0

    def fake_request(self, method, url, **kwargs):  # pragma: no cover - patched behaviour
        nonlocal call_count
        call_count += 1
        raise httpx.TimeoutException("timeout")

    monkeypatch.setattr(httpx.Client, "request", fake_request)

    with pytest.raises(httpx.TimeoutException):
        client.submit_checkpoint(peer, envelope)

    assert call_count == 3  # initial attempt + 2 retries
    counter = federation_metrics.client_retries_counter().collect()[0]
    sample = next(s for s in counter.samples if s.labels["peer"] == "node-athens")
    assert sample.value == 2.0
    client.close()


@pytest.mark.health
def test_transient_5xx_then_success(monkeypatch):
    peer = PeerRecord(id="node-athens", url="https://athens.example.net", pubkey="keys/a.pem", enabled=True)
    client = FederationClient(timeout_s=0.1, retries=2)
    envelope = _sample_envelope()

    request_obj = httpx.Request("POST", "https://athens.example.net/federation/checkpoint")
    responses = [
        httpx.Response(status_code=503, request=request_obj),
        httpx.Response(
            status_code=200,
            request=request_obj,
            json={"peer": "node-athens", "trust": {"verified": True, "score": 1.0}, "canonical_ts": envelope.canonical_ts(), "replayed": False},
        ),
    ]

    def fake_request(self, method, url, **kwargs):  # pragma: no cover - patched behaviour
        return responses.pop(0)

    monkeypatch.setattr(httpx.Client, "request", fake_request)

    result = client.submit_checkpoint(peer, envelope)
    assert result["peer"] == "node-athens"
    counter = federation_metrics.client_retries_counter().collect()[0]
    sample = next(s for s in counter.samples if s.labels["peer"] == "node-athens")
    assert sample.value == 1.0
    client.close()
