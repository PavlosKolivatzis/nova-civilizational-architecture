from orchestrator.temporal.engine import TemporalEngine


def test_temporal_engine_imports():
    engine = TemporalEngine()
    snapshot = engine.compute({})
    assert snapshot.data["status"] == "unimplemented"
