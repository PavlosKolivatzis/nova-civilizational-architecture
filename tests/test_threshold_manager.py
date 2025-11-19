import os

import pytest

from orchestrator.thresholds import get_threshold_manager, reset_threshold_manager_for_tests


def _fresh_manager(monkeypatch):
    for name in [
        "NOVA_SLOT07_TRI_DRIFT_THRESHOLD",
        "NOVA_SLOT07_STABILITY_THRESHOLD",
        "NOVA_SLOT07_STABILITY_THRESHOLD_TRI",
        "NOVA_SLOT06_TRI_MIN_SCORE",
    ]:
        monkeypatch.delenv(name, raising=False)
    reset_threshold_manager_for_tests()
    return get_threshold_manager()


def test_defaults_loaded(monkeypatch):
    mgr = _fresh_manager(monkeypatch)
    slot7 = mgr.get_slot7_thresholds()
    assert slot7.drift_threshold == pytest.approx(2.2)
    assert slot7.stability_threshold == pytest.approx(0.03)
    assert slot7.stability_threshold_tri == pytest.approx(0.05)
    assert slot7.effective_stability_threshold == pytest.approx(0.03)
    slot6 = mgr.get_slot6_thresholds()
    assert slot6.tri_min_score == pytest.approx(0.8)


def test_env_overrides(monkeypatch):
    monkeypatch.setenv("NOVA_SLOT07_TRI_DRIFT_THRESHOLD", "3.1")
    monkeypatch.setenv("NOVA_SLOT07_STABILITY_THRESHOLD", "0.07")
    monkeypatch.setenv("NOVA_SLOT07_STABILITY_THRESHOLD_TRI", "0.11")
    monkeypatch.setenv("NOVA_SLOT06_TRI_MIN_SCORE", "0.9")
    reset_threshold_manager_for_tests()
    mgr = get_threshold_manager()
    slot7 = mgr.get_slot7_thresholds()
    assert slot7.drift_threshold == pytest.approx(3.1)
    assert slot7.stability_threshold == pytest.approx(0.07)
    assert slot7.stability_threshold_tri == pytest.approx(0.11)
    slot6 = mgr.get_slot6_thresholds()
    assert slot6.tri_min_score == pytest.approx(0.9)


def test_tri_signal_adjusts_effective(monkeypatch):
    mgr = _fresh_manager(monkeypatch)
    mgr.update_from_tri_signal({"tri_drift_z": 3.0, "tri_band": "red", "tri_coherence": 0.4})
    slot7 = mgr.get_slot7_thresholds()
    assert slot7.effective_stability_threshold == pytest.approx(slot7.stability_threshold_tri)


def test_refresh_from_env_resets_effective(monkeypatch):
    mgr = _fresh_manager(monkeypatch)
    mgr.update_from_tri_signal({"tri_drift_z": 5.0, "tri_band": "red"})
    slot7 = mgr.get_slot7_thresholds()
    assert slot7.effective_stability_threshold == pytest.approx(slot7.stability_threshold_tri)
    monkeypatch.setenv("NOVA_SLOT07_STABILITY_THRESHOLD", "0.04")
    mgr.refresh_from_env()
    slot7_new = mgr.get_slot7_thresholds()
    assert slot7_new.stability_threshold == pytest.approx(0.04)
