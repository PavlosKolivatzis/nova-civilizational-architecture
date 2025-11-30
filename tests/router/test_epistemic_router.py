from nova.orchestrator.router.decision import ConstraintResult
from nova.orchestrator.router.epistemic_router import EpistemicRouter
from nova.orchestrator.router.anr_static_policy import StaticPolicyEngine, StaticPolicyConfig
from nova.orchestrator.router.temporal_constraints import TemporalConstraintResult
from nova.orchestrator.semantic_mirror import get_semantic_mirror, reset_semantic_mirror
from nova.orchestrator.thresholds import reset_threshold_manager_for_tests


class _StaticTemporalEngine:
    def __init__(self, result: TemporalConstraintResult):
        self._result = result

    def evaluate(self, payload):
        return self._result


def test_epistemic_router_passes_through_when_constraints_allow():
    def allow_constraints(request):
        return ConstraintResult(
            allowed=True,
            snapshot={"tri_signal": {"tri_coherence": 0.9}},
        )

    router = EpistemicRouter(
        constraint_fn=allow_constraints,
        policy_engine=StaticPolicyEngine(StaticPolicyConfig(base_score=0.8)),
        temporal_engine=_StaticTemporalEngine(
            TemporalConstraintResult(allowed=True, reason="ok", snapshot={"tri_coherence": 0.9})
        ),
    )
    decision = router.decide({"risk": 0.1, "novelty": 0.6})
    assert decision.route in ("primary", "low_trust")
    assert decision.constraints.allowed is True
    assert decision.final_score >= 0.0


def test_epistemic_router_forces_safe_mode_when_blocked():
    def deny_constraints(request):
        return ConstraintResult(allowed=False, reasons=["tri_low"])

    router = EpistemicRouter(
        constraint_fn=deny_constraints,
        temporal_engine=_StaticTemporalEngine(TemporalConstraintResult(allowed=True)),
    )
    decision = router.decide({"risk": 0.0})
    assert decision.route == "safe_mode"
    assert decision.final_score == 0.0


def test_temporal_penalty_reduces_score_and_sets_metadata():
    def allow_constraints(request):
        return ConstraintResult(
            allowed=True,
            snapshot={"tri_signal": {"tri_coherence": 0.95}},
        )

    temporal_result = TemporalConstraintResult(
        allowed=True,
        reason="temporal_variance_high",
        snapshot={"tri_coherence": 0.95, "temporal_variance": 0.6},
        penalty=0.4,
    )
    router = EpistemicRouter(
        constraint_fn=allow_constraints,
        policy_engine=StaticPolicyEngine(StaticPolicyConfig(base_score=0.9)),
        temporal_engine=_StaticTemporalEngine(temporal_result),
    )
    decision = router.decide({"risk": 0.2})
    assert decision.metadata["temporal_allowed"] is True
    assert decision.metadata["temporal"]["reason"] == "temporal_variance_high"
    assert decision.final_score < decision.policy.score


def test_temporal_block_forces_safe_mode():
    def allow_constraints(request):
        return ConstraintResult(
            allowed=True,
            snapshot={"tri_signal": {"tri_coherence": 0.8}},
        )

    temporal_result = TemporalConstraintResult(
        allowed=False,
        reason="temporal_drift_high",
        snapshot={"tri_coherence": 0.4, "temporal_drift": 0.8},
    )
    router = EpistemicRouter(
        constraint_fn=allow_constraints,
        temporal_engine=_StaticTemporalEngine(temporal_result),
    )
    decision = router.decide({"risk": 0.4})
    assert decision.route == "safe_mode"
    assert "temporal_drift_high" in decision.constraints.reasons


def test_router_publishes_temporal_router_modifiers():
    reset_semantic_mirror()
    router = EpistemicRouter()
    router.decide(
        {
            "tri_signal": {"tri_coherence": 0.85, "tri_drift_z": 0.1, "tri_jitter": 0.04},
            "slot07": {"mode": "BASELINE"},
            "slot10": {"passed": True},
        }
    )
    mirror = get_semantic_mirror()
    data = mirror.get_context("temporal.router_modifiers", "governance")
    try:
        assert data is not None
        assert data.get("allowed") is True
        assert "snapshot" in data
    finally:
        reset_semantic_mirror()


def test_predictive_penalty_reduces_score(monkeypatch):
    monkeypatch.setenv("NOVA_PREDICTIVE_COLLAPSE_THRESHOLD", "0.9")
    monkeypatch.setenv("NOVA_PREDICTIVE_ACCELERATION_THRESHOLD", "1.0")
    reset_threshold_manager_for_tests()

    def fake_snapshot(requester):
        return {"collapse_risk": 0.2, "drift_acceleration": 0.5}

    monkeypatch.setattr(
        "orchestrator.router.epistemic_router.read_predictive_snapshot",
        fake_snapshot,
    )
    router = EpistemicRouter()
    decision = router.decide({"tri_signal": {"tri_coherence": 0.95}, "slot07": {"mode": "BASELINE"}, "slot10": {"passed": True}})
    assert decision.route in ("primary", "low_trust")
    predictive_meta = decision.metadata["predictive"]
    assert predictive_meta["predictive_allowed"] is True
    assert predictive_meta["predictive_penalty"] > 0.0
    assert decision.final_score < decision.policy.score


def test_predictive_collapse_forces_safe_mode(monkeypatch):
    monkeypatch.setenv("NOVA_PREDICTIVE_COLLAPSE_THRESHOLD", "0.5")
    monkeypatch.setenv("NOVA_PREDICTIVE_ACCELERATION_THRESHOLD", "1.0")
    reset_threshold_manager_for_tests()

    def fake_snapshot(requester):
        return {"collapse_risk": 0.9, "drift_acceleration": 0.1}

    monkeypatch.setattr(
        "orchestrator.router.epistemic_router.read_predictive_snapshot",
        fake_snapshot,
    )
    router = EpistemicRouter()
    decision = router.decide(
        {"tri_signal": {"tri_coherence": 0.95}, "slot07": {"mode": "BASELINE"}, "slot10": {"passed": True}}
    )
    assert decision.route == "safe_mode"
    assert decision.metadata["predictive"]["reason"] == "foresight_hold"
