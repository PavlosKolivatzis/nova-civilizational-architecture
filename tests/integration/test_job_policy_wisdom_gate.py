"""
Integration test: Slot 7 wisdom-aware backpressure.

Verifies that:
1. ResourceProtector uses wisdom backpressure when enabled
2. Frozen state reduces max concurrent jobs
3. Low stability margin reduces parallelism
"""

import os

import pytest

from config.feature_flags import get_production_controls_config
from nova.governor import state as governor_state
from nova.orchestrator.thresholds.manager import reset_threshold_manager_for_tests
from nova.slots.slot07_production_controls.production_control_engine import (
    ProductionControlEngine,
)
from nova.slots.slot07_production_controls.wisdom_backpressure import (
    compute_max_concurrent_jobs,
)


def setup_function():
    """Reset state and enable wisdom backpressure."""
    governor_state.reset_for_tests(eta=0.10, frozen=False)
    os.environ["NOVA_WISDOM_BACKPRESSURE_ENABLED"] = "1"
    os.environ["NOVA_SLOT07_MAX_JOBS_BASELINE"] = "16"
    os.environ["NOVA_SLOT07_MAX_JOBS_FROZEN"] = "2"
    os.environ["NOVA_SLOT07_MAX_JOBS_REDUCED"] = "6"
    reset_threshold_manager_for_tests()


def teardown_function():
    """Clean up environment."""
    os.environ.pop("NOVA_WISDOM_BACKPRESSURE_ENABLED", None)
    os.environ.pop("NOVA_SLOT07_MAX_JOBS_BASELINE", None)
    os.environ.pop("NOVA_SLOT07_MAX_JOBS_FROZEN", None)
    os.environ.pop("NOVA_SLOT07_MAX_JOBS_REDUCED", None)


def test_baseline_parallelism_when_stable():
    """Test that stable system uses baseline parallelism."""
    governor_state.set_frozen(False)

    max_jobs = compute_max_concurrent_jobs(stability_margin=0.08)
    assert max_jobs == 16  # Baseline


def test_reduced_parallelism_when_tri_drift_high(monkeypatch):
    """High TRI drift should reduce parallelism."""
    governor_state.set_frozen(False)
    monkeypatch.setattr(
        "nova.slots.slot07_production_controls.wisdom_backpressure._read_tri_truth_signal",
        lambda: {"tri_drift_z": 5.0},
    )

    max_jobs = compute_max_concurrent_jobs(stability_margin=0.08)
    assert max_jobs == 6


def test_low_stability_freezes_system():
    """Critical stability drop should freeze production."""
    governor_state.set_frozen(False)
    max_jobs = compute_max_concurrent_jobs(stability_margin=0.01)
    assert max_jobs == 2


def test_minimal_parallelism_when_frozen():
    """Test that frozen state gives minimal parallelism."""
    governor_state.set_frozen(True)

    # Even with high stability, frozen state forces minimal jobs
    max_jobs = compute_max_concurrent_jobs(stability_margin=0.10)
    assert max_jobs == 2  # Frozen (minimal)


def test_production_control_engine_respects_backpressure():
    """Test that ProductionControlEngine uses wisdom backpressure."""
    config = get_production_controls_config()

    # Ensure resource protection is enabled
    config["resource_protection"]["enabled"] = True
    config["resource_protection"]["max_concurrent_requests"] = 16

    engine = ProductionControlEngine(config)

    # Get metrics to check effective max concurrent requests
    metrics = engine.resource_protector.get_metrics()

    # With wisdom backpressure enabled, should report effective_max
    assert "effective_max_concurrent_requests" in metrics
    assert "wisdom_backpressure_enabled" in metrics


def test_backpressure_integration_frozen_mode():
    """Test end-to-end backpressure in frozen mode."""
    governor_state.set_frozen(True)

    config = get_production_controls_config()
    config["resource_protection"]["enabled"] = True
    config["resource_protection"]["max_concurrent_requests"] = 16

    engine = ProductionControlEngine(config)
    metrics = engine.resource_protector.get_metrics()

    # Effective max should be frozen level (2), not baseline (16)
    if metrics.get("wisdom_backpressure_enabled"):
        assert metrics["effective_max_concurrent_requests"] == 2


def test_backpressure_disabled_uses_baseline():
    """Test that disabling backpressure uses baseline config."""
    os.environ["NOVA_WISDOM_BACKPRESSURE_ENABLED"] = "0"

    config = get_production_controls_config()
    config["resource_protection"]["enabled"] = True
    config["resource_protection"]["max_concurrent_requests"] = 16

    engine = ProductionControlEngine(config)
    metrics = engine.resource_protector.get_metrics()

    # Without wisdom backpressure, should use baseline
    assert metrics["max_concurrent_requests"] == 16
    if "wisdom_backpressure_enabled" in metrics:
        assert metrics["wisdom_backpressure_enabled"] is False


def test_backpressure_state_transitions():
    """Test backpressure responds to state transitions."""
    # Start stable
    governor_state.set_frozen(False)
    max_jobs_stable = compute_max_concurrent_jobs(stability_margin=0.08)
    assert max_jobs_stable == 16  # Baseline

    # Freeze
    governor_state.set_frozen(True)
    max_jobs_frozen = compute_max_concurrent_jobs(stability_margin=0.08)
    assert max_jobs_frozen == 2  # Frozen

    # Unfreeze
    governor_state.set_frozen(False)
    max_jobs_resumed = compute_max_concurrent_jobs(stability_margin=0.08)
    assert max_jobs_resumed == 16  # Back to baseline
