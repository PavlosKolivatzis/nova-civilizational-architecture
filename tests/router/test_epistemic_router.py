from orchestrator.router.decision import ConstraintResult
from orchestrator.router.epistemic_router import EpistemicRouter
from orchestrator.router.anr_static_policy import StaticPolicyEngine, StaticPolicyConfig


def test_epistemic_router_passes_through_when_constraints_allow():
    def allow_constraints(request):
        return ConstraintResult(
            allowed=True,
            snapshot={"tri_signal": {"tri_coherence": 0.9}},
        )

    router = EpistemicRouter(
        constraint_fn=allow_constraints,
        policy_engine=StaticPolicyEngine(StaticPolicyConfig(base_score=0.8)),
    )
    decision = router.decide({"risk": 0.1, "novelty": 0.6})
    assert decision.route in ("primary", "low_trust")
    assert decision.constraints.allowed is True
    assert decision.final_score >= 0.0


def test_epistemic_router_forces_safe_mode_when_blocked():
    def deny_constraints(request):
        return ConstraintResult(allowed=False, reasons=["tri_low"])

    router = EpistemicRouter(constraint_fn=deny_constraints)
    decision = router.decide({"risk": 0.0})
    assert decision.route == "safe_mode"
    assert decision.final_score == 0.0
