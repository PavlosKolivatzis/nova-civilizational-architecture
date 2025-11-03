import pytest


def test_no_peers_after_threshold_emits_event(monkeypatch):
    import orchestrator.federation_poller as fp
    from nova.federation.metrics import m

    metrics = m()
    evt = metrics["remediation_events"].labels(reason="no_peers")
    err = metrics["pull_result"].labels(status="error")
    base_evt = evt._value.get()
    base_err = err._value.get()

    monkeypatch.setenv("NOVA_FEDERATION_NO_PEER_THRESHOLD", "2")
    monkeypatch.setenv("NOVA_FEDERATION_NO_PEER_COOLDOWN", "0")
    monkeypatch.setattr(fp, "NO_PEERS_THRESHOLD", 2, raising=False)
    monkeypatch.setattr(fp, "NO_PEERS_COOLDOWN", 0, raising=False)

    fp._EMPTY_PEERS_STREAK = 0
    fp._LAST_EMPTY_PEERS_SIGNAL = 0.0

    fp._update_empty_peers([], metrics)
    fp._update_empty_peers([], metrics)
    assert evt._value.get() == pytest.approx(base_evt + 1)
    assert err._value.get() == pytest.approx(base_err + 1)
