from orchestrator.governance.engine import GovernanceEngine
from orchestrator.semantic_mirror import publish as mirror_publish, reset_semantic_mirror
from orchestrator.temporal.adapters import publish_router_modifiers
from orchestrator.predictive.trajectory_engine import PredictiveSnapshot
from orchestrator.thresholds import reset_threshold_manager_for_tests


class _StaticPredictiveEngine:
    def __init__(self, snapshots):
        if not isinstance(snapshots, list):
            snapshots = [snapshots]
        self._snapshots = list(snapshots)
        self._index = 0

    def predict(self, temporal):
        snapshot = self._snapshots[min(self._index, len(self._snapshots) - 1)]
        self._index += 1
        return snapshot


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


def test_governance_blocks_on_predictive_collapse():
    snapshot = PredictiveSnapshot(
        drift_velocity=0.0,
        drift_acceleration=0.0,
        stability_pressure=0.0,
        collapse_risk=0.95,
        safe_corridor=False,
        timestamp=10.0,
        raw={},
    )
    engine = GovernanceEngine(predictive_engine=_StaticPredictiveEngine(snapshot))
    result = engine.evaluate({"tri_signal": {"tri_coherence": 0.9}})
    assert result.allowed is False
    assert result.reason == "foresight_hold"


def test_governance_emits_predictive_warning(monkeypatch):
    monkeypatch.setenv("NOVA_PREDICTIVE_HISTORY_WINDOW", "2")
    monkeypatch.setenv("NOVA_PREDICTIVE_ACCELERATION_THRESHOLD", "0.01")
    reset_threshold_manager_for_tests()
    snapshots = [
        PredictiveSnapshot(
            drift_velocity=0.1,
            drift_acceleration=0.2,
            stability_pressure=0.1,
            collapse_risk=0.1,
            safe_corridor=True,
            timestamp=1.0,
            raw={},
        ),
        PredictiveSnapshot(
            drift_velocity=0.2,
            drift_acceleration=0.25,
            stability_pressure=0.1,
            collapse_risk=0.1,
            safe_corridor=True,
            timestamp=2.0,
            raw={},
        ),
    ]
    engine = GovernanceEngine(predictive_engine=_StaticPredictiveEngine(snapshots))
    engine.evaluate({"tri_signal": {"tri_coherence": 0.9, "tri_drift_z": 0.05}})
    result = engine.evaluate({"tri_signal": {"tri_coherence": 0.9, "tri_drift_z": 0.05}})
    assert result.allowed is True
    assert result.metadata.get("foresight_warning") == "predictive_acceleration"
