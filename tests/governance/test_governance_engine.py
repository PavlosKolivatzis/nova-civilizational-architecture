from orchestrator.governance.engine import GovernanceEngine


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
