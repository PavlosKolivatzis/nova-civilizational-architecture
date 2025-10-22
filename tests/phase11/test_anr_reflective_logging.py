"""Phase 11 ANR reflective logging tests."""

import pytest

from orchestrator.router.anr import AdaptiveNeuralRouter
from orchestrator.semantic_mirror import get_semantic_mirror, reset_semantic_mirror


@pytest.mark.health
def test_anr_explanation_context_published(monkeypatch):
    """ANR emits reflective explanation blob for each decision."""
    monkeypatch.setenv("NOVA_ANR_ENABLED", "1")
    monkeypatch.setenv("NOVA_ANR_PILOT", "0.1")

    reset_semantic_mirror()
    router = AdaptiveNeuralRouter()
    ctx = {
        "tri_drift_z": 0.05,
        "latency_norm": 0.02,
        "system_pressure": 0.1,
    }

    router.decide(ctx, shadow=False)

    mirror = get_semantic_mirror()
    explain = mirror.get_context("router.anr_explain", "anr")

    assert explain, "router.anr_explain context missing"
    assert explain["decision_id"]
    assert explain["live_route"] in router.ROUTES
    assert explain["shadow_best"] in router.ROUTES
    assert isinstance(explain["tri_delta_expected"], float)
    assert isinstance(explain["latency_cost"], float)
    assert "features_used" in explain
    assert explain["features_used"]["system_pressure"] == ctx["system_pressure"]
