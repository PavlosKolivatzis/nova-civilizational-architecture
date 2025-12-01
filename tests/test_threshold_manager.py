import importlib

from nova.orchestrator.thresholds.manager import (
    ThresholdManager,
    ThresholdConfig,
    get_threshold,
    snapshot_thresholds,
)


def test_defaults_load_correctly(monkeypatch):
    monkeypatch.delenv("NOVA_SLOT07_TRI_DRIFT_THRESHOLD", raising=False)
    mgr = ThresholdManager()
    snap = mgr.snapshot()
    assert snap["slot07_tri_drift_threshold"] == 2.2


def test_env_override(monkeypatch):
    monkeypatch.setenv("NOVA_SLOT07_TRI_DRIFT_THRESHOLD", "5.5")
    import nova.orchestrator.thresholds.manager as mgrmod

    importlib.reload(mgrmod)
    val = mgrmod.get_threshold("slot07_tri_drift_threshold")
    assert val == 5.5


def test_snapshot_returns_all_fields():
    snap = snapshot_thresholds()
    assert "tri_min_coherence" in snap
