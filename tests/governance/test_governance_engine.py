from orchestrator.governance.engine import GovernanceEngine
from orchestrator.semantic_mirror import publish as mirror_publish, reset_semantic_mirror
from orchestrator.temporal.adapters import publish_router_modifiers


def test_governance_engine_allows_stable_state():
    engine = GovernanceEngine()
    result = engine.evaluate(
        {
            "tri_signal": {"tri_coherence": 0.9, "tri_drift_z": 0.1, "tri_jitter": 0.05},
            "slot07": {"mode": "BASELINE"},
            "slot10": {"passed": True},
        }
    )
    assert result.allowed


def test_governance_engine_blocks_on_tri_low():
    engine = GovernanceEngine()
    result = engine.evaluate({"tri_signal": {"tri_coherence": 0.1}})
    assert not result.allowed
    assert result.reason == "tri_low"


def test_governance_engine_records_ledger():
    engine = GovernanceEngine()
    initial = len(engine.ledger.snapshot())
    engine.evaluate({"tri_signal": {"tri_coherence": 0.9}})
    assert len(engine.ledger.snapshot()) == initial + 1


def test_governance_reads_temporal_router_modifiers():
    reset_semantic_mirror()
    snapshot = {
        "timestamp": 1_700_000_000.0,
        "tri_coherence": 0.88,
        "tri_drift_z": 0.05,
        "slot07_mode": "BASELINE",
        "gate_state": True,
        "governance_state": "ok",
        "prediction_error": 0.05,
        "temporal_drift": 0.01,
        "temporal_variance": 0.02,
        "convergence_score": 0.97,
        "divergence_penalty": 0.02,
    }
    mirror_publish("temporal.snapshot", snapshot, "temporal", ttl=300.0)
    mirror_publish(
        "temporal.ledger_head",
        {"timestamp": snapshot["timestamp"], "hash": "abc123"},
        "temporal",
        ttl=300.0,
    )
    publish_router_modifiers(
        {"allowed": True, "reason": "ok", "penalty": 0.1, "snapshot": {"tri_coherence": 0.88}}
    )
    engine = GovernanceEngine()
    try:
        result = engine.evaluate({"tri_signal": {"tri_coherence": 0.88, "tri_drift_z": 0.05}})
        assert result.allowed is True
        assert "temporal_router_modifiers" in result.snapshot
        assert result.snapshot["temporal_router_modifiers"]["penalty"] == 0.1
        assert result.snapshot["temporal"]["tri_coherence"] == 0.88
    finally:
        reset_semantic_mirror()
