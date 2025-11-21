from orchestrator.governance.engine import GovernanceEngine
from orchestrator.router.epistemic_router import EpistemicRouter
from orchestrator.router.temporal_constraints import TemporalConstraintEngine
from orchestrator.temporal.ledger import TemporalLedger
from orchestrator.semantic_mirror import reset_semantic_mirror
from orchestrator.thresholds import reset_threshold_manager_for_tests


def _seed_ledger(coherences):
    ledger = TemporalLedger()
    timestamp = 1.0
    for value in coherences:
        ledger.append(
            {
                "timestamp": timestamp,
                "tri_coherence": value,
                "tri_drift_z": 0.0,
                "slot07_mode": "BASELINE",
                "gate_state": True,
                "governance_state": "ok",
                "prediction_error": 0.0,
                "temporal_drift": 0.0,
                "temporal_variance": 0.0,
                "convergence_score": 1.0,
                "divergence_penalty": 0.0,
            }
        )
        timestamp += 1.0
    return ledger


def test_temporal_drift_blocks_router():
    ledger = _seed_ledger([0.1])
    router = EpistemicRouter(temporal_engine=TemporalConstraintEngine(ledger=ledger))
    decision = router.decide(
        {
            "timestamp": 5.0,
            "tri_signal": {"tri_coherence": 0.9, "tri_drift_z": 0.1, "tri_jitter": 0.02},
            "slot07": {"mode": "BASELINE"},
            "slot10": {"passed": True},
        }
    )
    assert decision.route == "safe_mode"
    assert any(reason == "temporal_drift_high" for reason in decision.constraints.reasons)


def test_prediction_error_triggers_governance_hold():
    reset_semantic_mirror()
    engine = GovernanceEngine()
    result = engine.evaluate(
        {
            "prediction": 0.0,
            "tri_signal": {"tri_coherence": 0.9, "tri_drift_z": 0.05, "tri_jitter": 0.05},
            "slot07": {"mode": "BASELINE"},
            "slot10": {"passed": True},
        }
    )
    assert result.allowed is False
    assert result.reason == "temporal_prediction_error"


def test_high_variance_only_penalizes_router(monkeypatch):
    monkeypatch.setenv("NOVA_PREDICTIVE_COLLAPSE_THRESHOLD", "1.5")
    monkeypatch.setenv("NOVA_PREDICTIVE_ACCELERATION_THRESHOLD", "10.0")
    reset_threshold_manager_for_tests()
    ledger = _seed_ledger([0.0, 1.0, 0.0, 1.0])
    router = EpistemicRouter(temporal_engine=TemporalConstraintEngine(ledger=ledger))
    decision = router.decide(
        {
            "timestamp": 5.0,
            "tri_signal": {"tri_coherence": 0.95, "tri_drift_z": 0.1, "tri_jitter": 0.02},
            "slot07": {"mode": "BASELINE"},
            "slot10": {"passed": True},
        }
    )
    assert decision.route != "safe_mode"
    assert decision.metadata["temporal_penalty"] > 0.0
