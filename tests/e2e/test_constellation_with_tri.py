from slots.slot05_constellation.engine import ConstellationEngine
from slots.slot04_tri.engine import TRIEngine


def test_constellation_updates_with_tri_layers():
    c = ConstellationEngine()
    t = TRIEngine()
    before = c.get_current_position()
    lo = t.calculate("undeniable absolute consensus everyone knows")
    out = c.update_from_tri(lo["score"], lo["layer_scores"])
    after = out["position"]
    assert after != before
    assert out["stability_index"] < 0.95
