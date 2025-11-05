"""Test wisdom-aware backpressure for Slot 7."""

import os

import pytest

from nova.governor import state as governor_state
from nova.slots.slot07_production_controls import wisdom_backpressure as module


def setup_function():
    """Reset state and clear environment before each test."""
    governor_state.reset_for_tests(eta=0.10, frozen=False)
    # Clear env vars that might affect tests
    for key in ["NOVA_SLOT07_MAX_JOBS_BASELINE", "NOVA_SLOT07_MAX_JOBS_FROZEN",
                "NOVA_SLOT07_MAX_JOBS_REDUCED", "NOVA_SLOT07_STABILITY_THRESHOLD"]:
        os.environ.pop(key, None)


def test_baseline_when_stable():
    """Test that baseline parallelism is used when stable."""
    governor_state.set_frozen(False)

    # High stability margin → baseline
    max_jobs = module.compute_max_concurrent_jobs(stability_margin=0.08)
    assert max_jobs == 16  # Default baseline


def test_reduced_when_low_stability():
    """Test that parallelism is reduced when S < threshold."""
    governor_state.set_frozen(False)

    # Low stability margin (< 0.03 default) → reduced
    max_jobs = module.compute_max_concurrent_jobs(stability_margin=0.02)
    assert max_jobs == 6  # Default reduced


def test_frozen_overrides_stability():
    """Test that frozen state forces minimal parallelism regardless of S."""
    governor_state.set_frozen(True)

    # Even with high S, frozen state should force minimal jobs
    max_jobs = module.compute_max_concurrent_jobs(stability_margin=0.10)
    assert max_jobs == 2  # Default frozen


def test_frozen_minimal_parallelism():
    """Test that frozen state gives minimal parallelism."""
    governor_state.set_frozen(True)

    max_jobs = module.compute_max_concurrent_jobs()
    assert max_jobs <= 4  # Should be 2 by default


def test_config_from_environment():
    """Test reading configuration from environment."""
    os.environ["NOVA_SLOT07_MAX_JOBS_BASELINE"] = "32"
    os.environ["NOVA_SLOT07_MAX_JOBS_FROZEN"] = "4"
    os.environ["NOVA_SLOT07_MAX_JOBS_REDUCED"] = "12"
    os.environ["NOVA_SLOT07_STABILITY_THRESHOLD"] = "0.05"

    baseline, frozen, reduced, threshold = module.get_backpressure_config()

    assert baseline == 32
    assert frozen == 4
    assert reduced == 12
    assert threshold == pytest.approx(0.05)


def test_config_safety_constraints():
    """Test that config enforces safety constraints (frozen < reduced < baseline)."""
    os.environ["NOVA_SLOT07_MAX_JOBS_BASELINE"] = "10"
    os.environ["NOVA_SLOT07_MAX_JOBS_FROZEN"] = "8"  # Too high
    os.environ["NOVA_SLOT07_MAX_JOBS_REDUCED"] = "12"  # Too high

    baseline, frozen, reduced, threshold = module.get_backpressure_config()

    # Should be corrected
    assert frozen < reduced < baseline
    assert frozen <= baseline // 2


def test_none_stability_defaults_to_baseline():
    """Test that missing stability margin defaults to safe baseline."""
    governor_state.set_frozen(False)

    # No stability margin provided, poller unavailable → safe default
    max_jobs = module.compute_max_concurrent_jobs(stability_margin=None)
    assert max_jobs == 16  # Baseline (safe default)


def test_backpressure_status():
    """Test get_backpressure_status for monitoring."""
    governor_state.set_frozen(False)

    status = module.get_backpressure_status()

    assert "max_concurrent_jobs" in status
    assert "mode" in status
    assert "frozen" in status
    assert "config" in status
    assert status["frozen"] is False


def test_backpressure_status_frozen():
    """Test status correctly reports frozen mode."""
    governor_state.set_frozen(True)

    status = module.get_backpressure_status()

    assert status["mode"] == "FROZEN"
    assert status["frozen"] is True
    assert status["max_concurrent_jobs"] == 2  # Default frozen


def test_threshold_boundary():
    """Test behavior at stability threshold boundary."""
    threshold = 0.03  # Default

    # Just below threshold → reduced
    max_jobs_low = module.compute_max_concurrent_jobs(stability_margin=threshold - 0.001)
    assert max_jobs_low == 6  # Reduced

    # At or above threshold → baseline
    max_jobs_ok = module.compute_max_concurrent_jobs(stability_margin=threshold)
    assert max_jobs_ok == 16  # Baseline


def test_public_api():
    """Test that only intended symbols are exported."""
    public = {name for name in dir(module) if not name.startswith("_")}
    expected = {
        "compute_max_concurrent_jobs",
        "get_backpressure_config",
        "get_backpressure_status",
        "__all__",
        "os",
        "Tuple",
        "governor_state",
    }
    assert public <= expected

    exported = set(module.__all__)
    assert exported == {"compute_max_concurrent_jobs", "get_backpressure_config"}
