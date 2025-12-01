from nova.orchestrator.predictive.trajectory_engine import PredictiveTrajectoryEngine
from nova.orchestrator.predictive.ledger import PredictiveLedger
from nova.orchestrator.temporal.engine import TemporalSnapshot


def mock_snapshot(
    *,
    timestamp: float = 100.0,
    tri_coherence: float = 0.9,
    tri_drift_z: float = 0.0,
    slot07_mode: str = "BASELINE",
    gate_state: bool = True,
    governance_state: str = "ok",
    prediction_error: float = 0.0,
    temporal_drift: float = 0.0,
    temporal_variance: float = 0.0,
    convergence_score: float = 1.0,
    divergence_penalty: float = 0.0,
) -> TemporalSnapshot:
    return TemporalSnapshot(
        timestamp=timestamp,
        tri_coherence=tri_coherence,
        tri_drift_z=tri_drift_z,
        slot07_mode=slot07_mode,
        gate_state=gate_state,
        governance_state=governance_state,
        prediction_error=prediction_error,
        temporal_drift=temporal_drift,
        temporal_variance=temporal_variance,
        convergence_score=convergence_score,
        divergence_penalty=divergence_penalty,
        raw={"mock": True},
    )


def test_predictive_increasing_drift():
    engine = PredictiveTrajectoryEngine()
    engine.predict(mock_snapshot(timestamp=1.0, tri_drift_z=0.1))
    snap = engine.predict(mock_snapshot(timestamp=2.0, tri_drift_z=0.4))
    assert snap.drift_velocity > 0.0


def test_predictive_constant_drift():
    engine = PredictiveTrajectoryEngine()
    engine.predict(mock_snapshot(timestamp=5.0, tri_drift_z=0.2))
    snap = engine.predict(mock_snapshot(timestamp=7.0, tri_drift_z=0.2))
    assert abs(snap.drift_acceleration) < 1e-6


def test_pressure_spike_increases_risk():
    engine = PredictiveTrajectoryEngine()
    snap = engine.predict(
        mock_snapshot(
            timestamp=10.0,
            tri_drift_z=0.0,
            slot07_mode="FROZEN",
            prediction_error=0.3,
            temporal_variance=0.2,
        )
    )
    assert snap.collapse_risk > 0.0


def test_predictive_engine_appends_ledger():
    ledger = PredictiveLedger()
    engine = PredictiveTrajectoryEngine(ledger=ledger, horizon_seconds=30.0)
    engine.predict(mock_snapshot(timestamp=50.0, tri_coherence=0.88, tri_drift_z=0.1))
    head = ledger.head()
    assert head is not None
    assert head["entry"]["horizon_seconds"] == 30.0
    assert "drift_velocity" in head["entry"]
