"""Federation server endpoint tests."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest


@pytest.mark.health
def test_peers_endpoint_returns_configured_peer(client_factory):
    client = client_factory()
    res = client.get("/federation/peers")
    assert res.status_code == 200
    payload = res.json()
    assert payload["peers"][0]["id"] == "node-athens"


@pytest.mark.health
def test_checkpoint_accepts_known_peer(client_factory, make_envelope):
    client = client_factory()
    envelope = make_envelope()
    res = client.post("/federation/checkpoint", json=envelope.model_dump(mode="json"))
    assert res.status_code == 200
    body = res.json()
    assert body["peer"] == "node-athens"
    assert body["trust"]["verified"] is True
    assert body["canonical_ts"].endswith("Z")


@pytest.mark.health
def test_checkpoint_rejects_unknown_peer(client_factory, make_envelope):
    client = client_factory()
    envelope = make_envelope(producer="node-unknown")
    res = client.post("/federation/checkpoint", json=envelope.model_dump(mode="json"))
    assert res.status_code == 401
    assert res.json()["code"] == "unknown_peer"


@pytest.mark.health
def test_content_type_enforced(client_factory, make_envelope):
    client = client_factory()
    envelope = make_envelope()
    res = client.post(
        "/federation/checkpoint",
        content=envelope.canonical_json(),
        headers={"content-type": "text/plain"},
    )
    assert res.status_code == 415
    assert res.json()["code"] == "unsupported_media_type"


@pytest.mark.health
def test_body_size_limit(monkeypatch, make_envelope, client_factory):
    monkeypatch.setenv("NOVA_FEDERATION_BODY_MAX", "10")
    client = client_factory()
    res = client.post("/federation/checkpoint", json=make_envelope().model_dump(mode="json"))
    assert res.status_code == 413
    assert res.json()["code"] == "too_large"


@pytest.mark.health
def test_clock_skew_stale(monkeypatch, make_envelope, client_factory):
    monkeypatch.setenv("NOVA_FEDERATION_SKEW_S", "120")
    client = client_factory()
    old_ts = datetime.now(timezone.utc) - timedelta(seconds=130)
    env = make_envelope(ts=old_ts)
    res = client.post("/federation/checkpoint", json=env.model_dump(mode="json"))
    assert res.status_code == 422
    assert res.json()["code"] == "stale"


@pytest.mark.health
def test_clock_skew_future(monkeypatch, make_envelope, client_factory):
    monkeypatch.setenv("NOVA_FEDERATION_SKEW_S", "120")
    client = client_factory()
    future_ts = datetime.now(timezone.utc) + timedelta(seconds=130)
    env = make_envelope(ts=future_ts)
    res = client.post("/federation/checkpoint", json=env.model_dump(mode="json"))
    assert res.status_code == 422
    assert res.json()["code"] == "future"


@pytest.mark.health
def test_replay_block(monkeypatch, make_envelope, client_factory):
    monkeypatch.setenv("NOVA_FEDERATION_REPLAY_MODE", "block")
    client = client_factory()
    env = make_envelope()
    assert client.post("/federation/checkpoint", json=env.model_dump(mode="json")).status_code == 200
    replay = client.post("/federation/checkpoint", json=env.model_dump(mode="json"))
    assert replay.status_code == 409
    assert replay.json()["code"] == "replay"


@pytest.mark.health
def test_replay_mark(monkeypatch, make_envelope, client_factory):
    monkeypatch.setenv("NOVA_FEDERATION_REPLAY_MODE", "mark")
    client = client_factory()
    env = make_envelope()
    client.post("/federation/checkpoint", json=env.model_dump(mode="json"))
    replay = client.post("/federation/checkpoint", json=env.model_dump(mode="json"))
    assert replay.status_code == 200
    assert replay.json()["replayed"] is True


@pytest.mark.health
def test_rate_limited(monkeypatch, make_envelope, client_factory):
    monkeypatch.setenv("NOVA_FEDERATION_RATE_RPS", "0")
    monkeypatch.setenv("NOVA_FEDERATION_RATE_BURST", "1")
    client = client_factory()
    env = make_envelope()
    assert client.post("/federation/checkpoint", json=env.model_dump(mode="json")).status_code == 200
    second = client.post("/federation/checkpoint", json=make_envelope().model_dump(mode="json"))
    assert second.status_code == 429
    assert second.json()["code"] == "rate_limited"
