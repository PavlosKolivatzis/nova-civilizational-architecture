"""Ensure federation peer_last_seen gauge behaves."""

from nova.federation.metrics import m


def test_peer_last_seen_gauge_present():
    metrics = m()
    gauge = metrics["peer_last_seen"]

    # Should accept repeated label sets without duplicate registration errors.
    gauge.labels(peer="peer-1").set(123.0)
    gauge.labels(peer="peer-1").set(456.0)

    assert gauge.labels(peer="peer-1")._value.get() == 456.0
