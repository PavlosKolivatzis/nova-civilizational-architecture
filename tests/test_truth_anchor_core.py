from nova.slots.slot01_truth_anchor.truth_anchor_engine import TruthAnchorEngine


def test_engine_initializes_with_core_anchor():
    engine = TruthAnchorEngine()
    assert "nova.core" in engine._anchors
    snapshot = engine.snapshot()
    assert snapshot["anchors"] >= 1
    assert snapshot["total_anchors"] >= 1
    assert snapshot["active_anchors"] >= 1

