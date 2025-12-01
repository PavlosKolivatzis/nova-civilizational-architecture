import pytest

from nova.federation.metrics import m
from nova.orchestrator import federation_health


def test_peer_quality_metrics_exposed_in_health():
    metrics = m()
    metrics["peer_up"].labels(peer="peer-a").set(1.0)
    metrics["peer_last_seen"].labels(peer="peer-a").set(123.0)
    metrics["peer_quality"].labels(peer="peer-a").set(0.72)
    metrics["peer_p95"].labels(peer="peer-a").set(0.45)
    metrics["peer_success"].labels(peer="peer-a").set(0.9)

    payload = federation_health.get_peer_health()
    peer = next(p for p in payload["peers"] if p["id"] == "peer-a")
    assert peer["quality"] == pytest.approx(0.72)
    assert peer["success_rate"] == pytest.approx(0.9)
    assert peer["p95"] == pytest.approx(0.45)
