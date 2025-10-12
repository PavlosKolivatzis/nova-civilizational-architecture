
def test_constellation_updates_with_tri_layers(tmp_path, monkeypatch):
    # Enable TRI link for this test only
    monkeypatch.setenv("NOVA_ENABLE_TRI_LINK", "true")

    from nova.slots.slot05_constellation import ConstellationEngine
    from nova.slots.slot04_tri.core.tri_engine import TriEngine

    # Use temporary directories for test isolation
    model_dir = tmp_path / "tri_model"
    snapshot_dir = tmp_path / "tri_snapshots"
    model_dir.mkdir()
    snapshot_dir.mkdir()

    c = ConstellationEngine()
    t = TriEngine(model_dir, snapshot_dir)

    before = c.get_current_position()
    tri_result = t.calculate("undeniable absolute consensus everyone knows")
    out = c.update_from_tri(tri_result["score"], tri_result["layer_scores"])
    after = out["position"]

    assert after != before
    assert out["stability_index"] <= 0.95
    assert "tri_influence" in out
    assert out.get("disabled", False) is False

    # Extra sanity on TRI payload
    assert 0.0 <= tri_result["score"] <= 1.0
    assert {"structural", "semantic", "expression"} <= set(tri_result["layer_scores"])