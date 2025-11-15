import os
from nova.slots.slot10_civilizational_deployment.core.lightclock_gatekeeper import LightClockGatekeeper

class DummyMirror:
    def __init__(self, vals): self.vals = vals
    def read(self, key, default=None): return self.vals.get(key, default)

def test_gate_passes_when_all_good(monkeypatch):
    m = DummyMirror({"slot07.phase_lock": 0.9, "slot09.final_policy": "ALLOW_FASTPATH", "slot04.tri_score": 0.8})
    g = LightClockGatekeeper(mirror=m)
    res = g.evaluate_deploy_gate(slot08={}, slot04={"tri_score": 0.8})
    assert res.passed
    assert res.lightclock_passes
    assert res.coherence_level == "high"

def test_gate_blocks_on_low_tri(monkeypatch):
    m = DummyMirror({"slot07.phase_lock": 0.9, "slot09.final_policy": "ALLOW_FASTPATH"})
    g = LightClockGatekeeper(mirror=m)
    res = g.evaluate_deploy_gate(slot08={}, slot04={"tri_score": 0.5})
    assert not res.passed
    assert any("TRI" in f for f in res.failed_conditions)

def test_gate_blocks_on_low_phase_lock(monkeypatch):
    m = DummyMirror({"slot07.phase_lock": 0.5, "slot09.final_policy": "ALLOW_FASTPATH"})
    os.environ["NOVA_PHASE_LOCK_GATE"] = "0.7"
    g = LightClockGatekeeper(mirror=m)
    res = g.evaluate_deploy_gate(slot08={}, slot04={"tri_score": 0.8})
    assert not res.passed
    assert any("phase_lock" in f for f in res.failed_conditions)

def test_gate_blocks_on_slot9_policy(monkeypatch):
    m = DummyMirror({"slot07.phase_lock": 0.9, "slot09.final_policy": "DEGRADE_AND_REVIEW"})
    g = LightClockGatekeeper(mirror=m)
    res = g.evaluate_deploy_gate(slot08={}, slot04={"tri_score": 0.8})
    assert not res.passed
    assert any("slot9_policy" in f for f in res.failed_conditions)
