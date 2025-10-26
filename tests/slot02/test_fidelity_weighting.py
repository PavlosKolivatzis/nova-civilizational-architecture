"""Tests for Slot02 fidelity weighting service."""

from types import SimpleNamespace

import pytest

from nova.slots.slot01_truth_anchor.quantum_entropy import EntropySample
from nova.slots.slot02_deltathresh.config import FidelityWeightingConfig, ProcessingConfig
from nova.slots.slot02_deltathresh.core import DeltaThreshProcessor
from nova.slots.slot02_deltathresh.fidelity_weighting import FidelityWeightingService


@pytest.fixture
def sample_entropy():
    return EntropySample(
        data=b"\xAA" * 32,
        source="quantum",
        backend="simulator",
        fidelity=1.0,
        fidelity_ci=(0.95, 1.0),
        abs_bias=0.0,
    )


def test_fidelity_service_clamps_weights(monkeypatch, sample_entropy):
    cfg = FidelityWeightingConfig(enabled=True, base=1.0, slope=5.0, clamp_lo=0.9, clamp_hi=1.1)
    service = FidelityWeightingService(cfg)

    low_sample = EntropySample(
        data=b"\xFF" * 32,
        source="fallback",
        backend="os.urandom",
        fidelity=0.7,
        fidelity_ci=(0.3, 0.9),
        abs_bias=0.3,
    )
    samples = [sample_entropy, low_sample]

    monkeypatch.setattr(
        "nova.slots.slot02_deltathresh.fidelity_weighting.get_entropy_sample",
        lambda *_: samples.pop(0),
    )

    weight_high, _ = service.compute_weight()
    assert weight_high == pytest.approx(cfg.clamp_hi, rel=1e-3)

    weight_low, _ = service.compute_weight()
    assert weight_low == pytest.approx(cfg.clamp_lo, rel=1e-3)


def test_processor_applies_fidelity_weighting(monkeypatch):
    cfg_disabled = ProcessingConfig()
    cfg_disabled.fidelity_weighting.enabled = False

    cfg_enabled = ProcessingConfig()
    cfg_enabled.fidelity_weighting.enabled = True
    cfg_enabled.fidelity_weighting.base = 1.0
    cfg_enabled.fidelity_weighting.slope = 0.5
    cfg_enabled.fidelity_weighting.clamp_hi = 1.2

    proc_disabled = DeltaThreshProcessor(config=cfg_disabled)
    proc_enabled = DeltaThreshProcessor(config=cfg_enabled)

    monkeypatch.setattr(proc_disabled, "_calculate_tri_score", lambda content: 0.84)
    monkeypatch.setattr(proc_enabled, "_calculate_tri_score", lambda content: 0.84)

    monkeypatch.setattr(proc_disabled.pattern_detector, "detect_patterns", lambda content: {"delta": 0.65})
    monkeypatch.setattr(proc_enabled.pattern_detector, "detect_patterns", lambda content: {"delta": 0.65})

    proc_enabled._fidelity_service = SimpleNamespace(compute_weight=lambda: (1.1, None))

    result_disabled = proc_disabled.process_content("content", session_id="t1")
    assert result_disabled.action != "allow"

    result_enabled = proc_enabled.process_content("content", session_id="t2")
    assert result_enabled.action == "allow"
    assert proc_enabled._last_fidelity_weight == pytest.approx(1.1, rel=1e-3)
