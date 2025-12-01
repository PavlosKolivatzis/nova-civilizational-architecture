import time

import pytest

pytest.importorskip("fastapi")
from fastapi.testclient import TestClient

from nova.federation.metrics import m


def _client():
    from nova.orchestrator.app import app

    return TestClient(app)


def test_quality_gating_controls_ready(monkeypatch):
    from nova.orchestrator import federation_poller as poller

    monkeypatch.setenv("NOVA_FED_MIN_PEER_QUALITY", "0.6")
    monkeypatch.setenv("NOVA_FED_MIN_GOOD_PEERS", "1")

    metrics = m()
    poller.reset_peer_quality_state()

    metrics["peer_up"].labels(peer="peer-a").set(1.0)
    metrics["peer_last_seen"].labels(peer="peer-a").set(time.time())
    metrics["peer_quality"].labels(peer="peer-a").set(0.5)
    metrics["peer_p95"].labels(peer="peer-a").set(1.2)
    metrics["peer_success"].labels(peer="peer-a").set(0.5)
    metrics["last_result_ts"].labels(status="success").set(time.time())

    low_scores = {"peer-a": 0.5}
    poller._apply_quality_gate(True, low_scores, metrics)

    resp = _client().get("/ready")
    assert resp.status_code == 503
    assert resp.json()["ready"] is False

    metrics["peer_quality"].labels(peer="peer-a").set(0.85)
    metrics["peer_success"].labels(peer="peer-a").set(0.9)

    high_scores = {"peer-a": 0.85}
    poller._apply_quality_gate(True, high_scores, metrics)

    resp = _client().get("/ready")
    assert resp.status_code == 200
    assert resp.json()["ready"] is True
