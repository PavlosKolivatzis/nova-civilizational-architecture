import pytest
np = pytest.importorskip("numpy")

from orchestrator.router.anr import AdaptiveNeuralRouter

def test_linucb_learns_in_shadow(tmp_path, monkeypatch):
    monkeypatch.setenv("NOVA_ANR_STATE_PATH", str(tmp_path / "linucb.json"))
    monkeypatch.setenv("NOVA_ANR_LEARN_SHADOW", "1")
    r = AdaptiveNeuralRouter()
    assert r._bandit_store is not None

    ctx = {"cultural_residual_risk": 0.9, "system_pressure": 0.2}
    d = r.decide(ctx, shadow=True)

    # immediate: good TRI delta, moderate latency
    r.credit_immediate(d.id, latency_s=0.6, tri_delta=0.1)
    # deploy: OK, low error, modest transform
    r.credit_deployment({
        "decision_id": d.id, "slo_ok": True, "error_rate": 0.02,
        "transform_rate": 0.15, "rollback": False
    })

    # state file should exist & be non-empty
    path = r.bandit_state_path
    import os
    assert os.path.exists(path) and os.path.getsize(path) > 0