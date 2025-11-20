from orchestrator.router.anr_static_policy import StaticPolicyEngine, StaticPolicyConfig


def test_static_policy_scoring_balances_features():
    engine = StaticPolicyEngine(StaticPolicyConfig())
    result = engine.evaluate({"risk": 0.2, "novelty": 0.7, "urgency": 0.6})
    assert result.route == "primary"
    assert 0.0 <= result.score <= 1.0


def test_static_policy_enters_safe_mode_when_score_low():
    engine = StaticPolicyEngine(StaticPolicyConfig(base_score=0.2))
    result = engine.evaluate({"risk": 1.0, "novelty": 0.0, "urgency": 0.0})
    assert result.route == "safe_mode"
