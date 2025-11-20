import pytest

from orchestrator.temporal.engine import TemporalEngine
from orchestrator.temporal.ledger import TemporalLedger


def test_temporal_engine_computes_drift_and_error():
    ledger = TemporalLedger()
    engine = TemporalEngine(ledger)

    engine.compute({"tri_signal": {"tri_coherence": 0.9, "tri_drift_z": 0.1}, "timestamp": 1.0})
    snapshot = engine.compute(
        {
            "tri_signal": {"tri_coherence": 0.4, "tri_drift_z": 0.2},
            "timestamp": 2.0,
            "prediction": 0.6,
            "slot07": {"mode": "BASELINE"},
            "slot10": {"passed": True},
        }
    )

    assert snapshot.temporal_drift == pytest.approx(0.5, rel=1e-6)
    assert snapshot.prediction_error == pytest.approx(0.2, rel=1e-6)
    assert len(ledger.snapshot()) == 2


def test_temporal_engine_handles_stable_state():
    ledger = TemporalLedger()
    engine = TemporalEngine(ledger)
    first = engine.compute({"tri_signal": {"tri_coherence": 0.8}, "timestamp": 1.0})
    second = engine.compute({"tri_signal": {"tri_coherence": 0.82}, "timestamp": 2.0})

    assert first.temporal_drift == pytest.approx(0.0)
    assert second.temporal_drift == pytest.approx(0.02)
