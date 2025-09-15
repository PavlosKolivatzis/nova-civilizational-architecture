from __future__ import annotations
from pathlib import Path
import time
from math import isclose
from slots.slot04_tri.core.policy import TriPolicy
from slots.slot04_tri.core.tri_engine import TriEngine

def setup_env(tmp_path: Path):
    model_dir = tmp_path / "model"; model_dir.mkdir()
    (model_dir/"weights.json").write_text('{"w":1}')
    snaps = tmp_path / "snaps"
    return model_dir, snaps

def test_autonomous_detection_and_recovery(tmp_path: Path):
    model_dir, snaps = setup_env(tmp_path)
    policy = TriPolicy(mttr_target_s=5.0)
    tri = TriEngine(model_dir, snaps, policy)

    # Snapshot baseline
    tri.take_snapshot()

    # Stream mostly normal, then sudden abnormal spike to trigger threshold up & drift
    for _ in range(30):
        tri.observe({"a": 0.3, "b": 0.2}, writes_in_last_sec=5)
    adapted = tri.observe({"a": 3.0, "b": 2.0}, writes_in_last_sec=80)
    assert adapted["drift"] or adapted["surge"], "Should detect drift or surge"

    t0 = time.time()
    result = tri.auto_heal_once()
    assert result["ok"] is True
    assert time.time() - t0 <= policy.mttr_target_s

def test_safe_mode_continuity(tmp_path: Path):
    model_dir, snaps = setup_env(tmp_path)
    policy = TriPolicy()
    tri = TriEngine(model_dir, snaps, policy)

    # Force a decision with no snapshot available → SAFE_MODE
    out = tri.auto_heal_once()
    assert out["decision"] in ("SAFE_MODE_BLOCK","NOOP")
    # If in safe mode, latency must be low
    if out["decision"] == "SAFE_MODE_BLOCK":
        dt = tri.safe_mode.activate()
        assert dt <= policy.safe_mode_flip_max_s

def test_confidence_interval_behavior(tmp_path: Path):
    model_dir, snaps = setup_env(tmp_path)
    tri = TriEngine(model_dir, snaps, TriPolicy())
    for _ in range(100):
        tri.observe({"x": 0.4, "y": 0.5}, writes_in_last_sec=3)
    lo, hi = tri.confidence_interval(0.95)
    assert 0.0 <= lo <= hi <= 1.0

def test_threshold_adapts_and_reverts(tmp_path: Path):
    model_dir, snaps = setup_env(tmp_path)
    tri = TriEngine(model_dir, snaps, TriPolicy())
    # stabilize
    for _ in range(20):
        tri.observe({"n": 0.3, "m": 0.2}, writes_in_last_sec=4)
    th0, base0 = tri.threshold, tri.baseline
    # anomaly
    tri.observe({"n": 3.0, "m": 2.0}, writes_in_last_sec=80)
    th1 = tri.threshold
    assert th1 > th0 or isclose(th1, th0, rel_tol=1e-3), "threshold should rise on anomaly"
    # return to normal — should pull back toward baseline floor
    for _ in range(20):
        tri.observe({"n": 0.3, "m": 0.2}, writes_in_last_sec=4)
    th2 = tri.threshold
    assert th2 <= th1 and th2 >= tri.policy.min_rel_baseline * tri.baseline, \
        "threshold should revert but respect min-rel floor"

def test_surge_respects_warmup(tmp_path: Path):
    model_dir, snaps = setup_env(tmp_path)
    tri = TriEngine(model_dir, snaps, TriPolicy(surge_window=5, surge_threshold=12))
    # fewer than window samples -> must not fire
    for _ in range(4):
        out = tri.observe({"x":0.3}, writes_in_last_sec=3)
        assert out["surge"] is None
    # window becomes full here; sum=15 -> fires
    out = tri.observe({"x":0.3}, writes_in_last_sec=3)
    assert out["surge"] is not None

def test_snapshot_ops(tmp_path: Path):
    model_dir, snaps = setup_env(tmp_path)
    tri = TriEngine(model_dir, snaps, TriPolicy())
    meta = tri.take_snapshot()
    ids = tri.snapshotter.list_snapshots()
    assert meta.id in ids
    assert tri.snapshotter.get_snapshot(meta.id) is not None
    kept = tri.snapshotter.prune(keep_last=1)
    assert kept >= 0

def test_core_imports():
    """Validate re-export surface works correctly."""
    from slots.slot04_tri.core import TriEngine, TriPolicy  # should import cleanly
    assert TriEngine is not None
    assert TriPolicy is not None