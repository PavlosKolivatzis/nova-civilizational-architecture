import os

import pytest

from orchestrator.thresholds.manager import reset_threshold_manager_for_tests
from nova.slots.slot10_civilizational_deployment.core.lightclock_gatekeeper import LightClockGatekeeper


class DummyMirror:
    def __init__(self, vals):
        self.vals = vals

    def read(self, key, default=None):
        return self.vals.get(key, default)


def setup_function():
    reset_threshold_manager_for_tests()
    for key in ["NOVA_TRI_GATE", "NOVA_PHASE_LOCK_GATE", "NOVA_SLOT9_ALLOWED"]:
        os.environ.pop(key, None)


def test_gate_passes_with_high_coherence_and_low_drift():
    mirror = DummyMirror(
        {
            "slot07.phase_lock": 0.9,
            "slot09.final_policy": "ALLOW_FASTPATH",
            "slot04.tri_truth_signal": {"tri_coherence": 0.82, "tri_drift_z": 0.5, "tri_jitter": 0.05},
        }
    )
    gate = LightClockGatekeeper(mirror=mirror)
    result = gate.evaluate_deploy_gate(slot08={}, slot04={})
    assert result.passed
    assert result.lightclock_reason == "ok"


def test_gate_blocks_on_low_tri_coherence():
    mirror = DummyMirror(
        {
            "slot07.phase_lock": 0.9,
            "slot09.final_policy": "ALLOW_FASTPATH",
            "slot04.tri_truth_signal": {"tri_coherence": 0.4, "tri_drift_z": 0.2},
        }
    )
    gate = LightClockGatekeeper(mirror=mirror)
    result = gate.evaluate_deploy_gate(slot08={}, slot04={})
    assert not result.passed
    assert any("tri_coherence" in reason for reason in result.failed_conditions)


def test_gate_blocks_on_drift_threshold():
    mirror = DummyMirror(
        {
            "slot07.phase_lock": 0.9,
            "slot09.final_policy": "ALLOW_FASTPATH",
            "slot04.tri_truth_signal": {"tri_coherence": 0.9, "tri_drift_z": 9.0},
        }
    )
    gate = LightClockGatekeeper(mirror=mirror)
    result = gate.evaluate_deploy_gate(slot08={}, slot04={})
    assert not result.passed
    assert any("tri_drift" in reason for reason in result.failed_conditions)


def test_gate_respects_phase_lock_gate():
    os.environ["NOVA_PHASE_LOCK_GATE"] = "0.8"
    mirror = DummyMirror(
        {
            "slot07.phase_lock": 0.6,
            "slot09.final_policy": "ALLOW_FASTPATH",
            "slot04.tri_truth_signal": {"tri_coherence": 0.9},
        }
    )
    gate = LightClockGatekeeper(mirror=mirror)
    result = gate.evaluate_deploy_gate(slot08={}, slot04={})
    assert not result.passed
    assert any("phase_lock" in reason for reason in result.failed_conditions)


def test_gate_blocks_on_slot9_policy():
    mirror = DummyMirror(
        {
            "slot07.phase_lock": 0.9,
            "slot09.final_policy": "DEGRADE_AND_REVIEW",
            "slot04.tri_truth_signal": {"tri_coherence": 0.85},
        }
    )
    gate = LightClockGatekeeper(mirror=mirror)
    result = gate.evaluate_deploy_gate(slot08={}, slot04={})
    assert not result.passed
    assert any("slot9_policy" in reason for reason in result.failed_conditions)


def test_env_override_for_tri_gate():
    os.environ["NOVA_TRI_GATE"] = "0.9"
    mirror = DummyMirror(
        {
            "slot07.phase_lock": 0.9,
            "slot09.final_policy": "ALLOW_FASTPATH",
            "slot04.tri_truth_signal": {"tri_coherence": 0.88},
        }
    )
    gate = LightClockGatekeeper(mirror=mirror)
    result = gate.evaluate_deploy_gate(slot08={}, slot04={})
    assert not result.passed
    assert any("tri_coherence" in reason for reason in result.failed_conditions)


def test_gate_deterministic_under_noise(monkeypatch):
    sequence = [0.1, 0.3, 0.1, 0.2]

    class NoisyMirror(DummyMirror):
        def read(self, key, default=None):
            if key == "slot04.tri_truth_signal":
                val = sequence.pop(0)
                sequence.append(val)
                return {"tri_coherence": 0.85, "tri_jitter": val}
            return super().read(key, default)

    mirror = NoisyMirror({"slot07.phase_lock": 0.9, "slot09.final_policy": "ALLOW_FASTPATH"})
    gate = LightClockGatekeeper(mirror=mirror)
    first = gate.evaluate_deploy_gate(slot08={}, slot04={})
    second = gate.evaluate_deploy_gate(slot08={}, slot04={})
    assert first.passed == second.passed
