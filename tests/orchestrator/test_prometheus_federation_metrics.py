from nova.federation.metrics import m

def test_prometheus_response_includes_federation_metrics(monkeypatch):
    from nova.orchestrator import prometheus_metrics as pm

    # Avoid heavy imports during the update phase
    monkeypatch.setattr(pm, "update_slot6_metrics", lambda: None)
    monkeypatch.setattr(pm, "update_flag_metrics", lambda: None)
    monkeypatch.setattr(pm, "update_slot1_metrics", lambda: None)
    monkeypatch.setattr(pm, "update_lightclock_metrics", lambda: None)
    monkeypatch.setattr(pm, "update_system_health_metrics", lambda: None)
    monkeypatch.setattr(pm, "update_semantic_mirror_metrics", lambda: None)

    metrics = m()
    metrics["peers"].set(4)
    metrics["peer_up"].labels(peer="node-a").set(1.0)
    metrics["peer_last_seen"].labels(peer="node-a").set(123.0)
    metrics["ready"].set(1.0)

    payload, content_type = pm.get_metrics_response()

    assert content_type == pm.CONTENT_TYPE_LATEST
    assert b"nova_federation_peers" in payload
    assert b" 4" in payload
    assert b"nova_federation_peer_up" in payload
    assert b"nova_federation_peer_last_seen" in payload
    assert b"nova_federation_ready" in payload
