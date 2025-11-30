"""Test wisdom-aware backpressure for Slot 7."""

import os

import pytest

from nova.governor import state as governor_state
from nova.orchestrator.thresholds.manager import reset_threshold_manager_for_tests
from nova.slots.slot07_production_controls import wisdom_backpressure as module


def setup_function():
    """Reset state and clear environment before each test."""
    governor_state.reset_for_tests(eta=0.10, frozen=False)
    for key in [
        "NOVA_SLOT07_MAX_JOBS_BASELINE",
        "NOVA_SLOT07_MAX_JOBS_FROZEN",
        "NOVA_SLOT07_MAX_JOBS_REDUCED",
        "NOVA_SLOT07_STABILITY_THRESHOLD",
        "NOVA_SLOT07_STABILITY_THRESHOLD_TRI",
        "NOVA_SLOT07_TRI_DRIFT_THRESHOLD",
    ]:
        os.environ.pop(key, None)
    reset_threshold_manager_for_tests()
    module._tri_signal_snapshot.clear()


def test_baseline_when_stable():
    """Test that baseline parallelism is used when stable."""
    governor_state.set_frozen(False)
    max_jobs = module.compute_max_concurrent_jobs(stability_margin=0.08)
    assert max_jobs == 16


def test_tri_drift_reduces_parallelism(monkeypatch):
    """High TRI drift should reduce concurrency."""
    governor_state.set_frozen(False)
    monkeypatch.setattr(module, "_read_tri_truth_signal", lambda: {"tri_drift_z": 5.0})
    max_jobs = module.compute_max_concurrent_jobs(stability_margin=0.08)
    assert max_jobs == 6


def test_low_stability_triggers_freeze():
    """Critical stability drop freezes production."""
    governor_state.set_frozen(False)
    max_jobs = module.compute_max_concurrent_jobs(stability_margin=0.01)
    assert max_jobs == 2


def test_frozen_overrides_stability():
    """Frozen state forces minimal parallelism regardless of S."""
    governor_state.set_frozen(True)
    max_jobs = module.compute_max_concurrent_jobs(stability_margin=0.10)
    assert max_jobs == 2


def test_frozen_minimal_parallelism():
    """Frozen state gives minimal parallelism even without S."""
    governor_state.set_frozen(True)
    max_jobs = module.compute_max_concurrent_jobs()
    assert max_jobs <= 4


def test_config_from_environment():
    """Test reading configuration from environment."""
    os.environ["NOVA_SLOT07_MAX_JOBS_BASELINE"] = "32"
    os.environ["NOVA_SLOT07_MAX_JOBS_FROZEN"] = "4"
    os.environ["NOVA_SLOT07_MAX_JOBS_REDUCED"] = "12"
    os.environ["NOVA_SLOT07_STABILITY_THRESHOLD"] = "0.05"
    reset_threshold_manager_for_tests()

    baseline, frozen, reduced, threshold = module.get_backpressure_config()
    assert baseline == 32
    assert frozen == 4
    assert reduced == 12
    assert threshold == pytest.approx(0.05)


def test_config_safety_constraints():
    """Test that config enforces safety constraints (frozen < reduced < baseline)."""
    os.environ["NOVA_SLOT07_MAX_JOBS_BASELINE"] = "10"
    os.environ["NOVA_SLOT07_MAX_JOBS_FROZEN"] = "8"
    os.environ["NOVA_SLOT07_MAX_JOBS_REDUCED"] = "12"
    reset_threshold_manager_for_tests()

    baseline, frozen, reduced, _ = module.get_backpressure_config()
    assert frozen < reduced < baseline
    assert frozen <= baseline // 2


def test_none_stability_defaults_to_baseline():
    """Test that missing stability margin defaults to safe baseline."""
    governor_state.set_frozen(False)
    max_jobs = module.compute_max_concurrent_jobs(stability_margin=None)
    assert max_jobs == 16


def test_backpressure_status():
    """Test get_backpressure_status for monitoring."""
    governor_state.set_frozen(False)
    status = module.get_backpressure_status()
    assert "max_concurrent_jobs" in status
    assert "config" in status
    assert status["frozen"] is False
    assert "thresholds" in status["config"]


def test_backpressure_status_frozen():
    """Test status correctly reports frozen mode."""
    governor_state.set_frozen(True)
    status = module.get_backpressure_status()
    assert status["mode"] == "FROZEN"
    assert status["max_concurrent_jobs"] == 2


def test_threshold_boundary():
    """Test behavior at stability threshold boundaries."""
    os.environ["NOVA_SLOT07_STABILITY_THRESHOLD"] = "0.03"
    os.environ["NOVA_SLOT07_STABILITY_THRESHOLD_TRI"] = "0.015"
    reset_threshold_manager_for_tests()
    governor_state.set_frozen(False)

    # Between freeze and reduce -> reduced
    max_jobs_reduced = module.compute_max_concurrent_jobs(stability_margin=0.02)
    assert max_jobs_reduced == 6

    # Below freeze threshold -> frozen
    max_jobs_frozen = module.compute_max_concurrent_jobs(stability_margin=0.005)
    assert max_jobs_frozen == 2

    # Healthy S -> baseline
    max_jobs_ok = module.compute_max_concurrent_jobs(stability_margin=0.08)
    assert max_jobs_ok == 16


def test_semantic_mirror_publication(monkeypatch):
    """Ensure semantic mirror publishes backpressure diagnostics."""
    published = {}

    def fake_publish(key, value, publisher, ttl):
        published["key"] = key
        published["value"] = value
        published["publisher"] = publisher
        published["ttl"] = ttl
        return True

    monkeypatch.setattr(module, "_publish_context", fake_publish)
    governor_state.set_frozen(False)
    module.compute_max_concurrent_jobs(stability_margin=0.08)

    assert published.get("key") == "slot07.backpressure_state"
    assert published.get("publisher") == "slot07_production_controls"
    assert published.get("value", {}).get("cap") == 16


def test_public_api():
    """Test that only intended symbols are exported."""
    public = {name for name in dir(module) if not name.startswith("_")}
    expected = {
        "compute_max_concurrent_jobs",
        "get_backpressure_config",
        "get_backpressure_status",
        "get_tri_signal_snapshot",
        "__all__",
        "annotations",
        "os",
        "Tuple",
        "governor_state",
        "get_threshold",
        "snapshot_thresholds",
    }
    assert public <= expected
    assert set(module.__all__) == {
        "compute_max_concurrent_jobs",
        "get_backpressure_config",
        "get_tri_signal_snapshot",
    }
