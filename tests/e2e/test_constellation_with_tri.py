import pytest

@pytest.mark.skipif("True", reason="Phase 1 skeleton; enable after wiring")
def test_constellation_updates_with_tri_layers():
    from slots.slot05_constellation.core import ConstellationEngine
    from slots.slot04_tri.core import TRIEngine
    c = ConstellationEngine()
    t = TRIEngine()
    before = c.get_current_position()
    tri_result = t.calculate("undeniable absolute consensus everyone knows")
    out = c.update_from_tri(tri_result["score"], tri_result["layer_scores"])
    after = out["position"]
    assert after != before
    assert out["stability_index"] < 0.95