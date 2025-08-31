from slots.slot01_truth_anchor.truth_anchor_engine import TruthAnchorEngine


def test_core_anchor_metrics_stable_across_recoveries():
    engine = TruthAnchorEngine()
    engine._establish_core_anchor()
    initial = (
        engine.anchor_metrics.total_anchors,
        engine.anchor_metrics.active_anchors,
    )

    for _ in range(3):
        engine._anchors["nova.core"].value = b"corrupt"
        engine._establish_core_anchor()
        assert engine._anchors["nova.core"].value == engine.export_secret_key()

    assert (
        engine.anchor_metrics.total_anchors,
        engine.anchor_metrics.active_anchors,
    ) == initial
