from orchestrator.router.epistemic_router import EpistemicRouter


def test_routing_pipeline_primary_path():
    router = EpistemicRouter()
    decision = router.decide(
        {
            "tri_signal": {"tri_coherence": 0.9, "tri_drift_z": 0.1, "tri_jitter": 0.05},
            "slot07": {"mode": "BASELINE"},
            "slot10": {"passed": True},
            "risk": 0.2,
            "novelty": 0.8,
        }
    )
    assert decision.route in ("primary", "low_trust")
    assert decision.constraints.allowed is True


def test_routing_pipeline_enters_safe_mode_when_tri_low():
    router = EpistemicRouter()
    decision = router.decide(
        {
            "tri_signal": {"tri_coherence": 0.2, "tri_drift_z": 5.0},
            "slot07": {"mode": "BASELINE"},
            "slot10": {"passed": True},
        }
    )
    assert decision.route == "safe_mode"
    assert decision.constraints.allowed is False
