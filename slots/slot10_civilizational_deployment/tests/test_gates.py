from __future__ import annotations
from slots.slot10_civilizational_deployment.core import Slot10Policy, Gatekeeper

def green():
    return {
        "slot08": {"integrity_score": 0.95, "quarantine_active": False, "recent_recoveries": {"success_rate_5m": 0.95}},
        "slot04": {"safe_mode_active": False, "drift_z": 0.5},
    }

def test_gate_block_on_quarantine():
    policy = Slot10Policy()
    gk = Gatekeeper(policy)
    m = green()
    m["slot08"]["quarantine_active"] = True
    res = gk.evaluate_deploy_gate(m["slot08"], m["slot04"])
    assert res.passed is False and "slot08_quarantine" in res.failed_conditions

def test_gate_block_on_drift():
    policy = Slot10Policy()
    gk = Gatekeeper(policy)
    m = green()
    m["slot04"]["drift_z"] = policy.slot04_drift_z_threshold  # >= threshold should block
    res = gk.evaluate_deploy_gate(m["slot08"], m["slot04"])
    assert res.passed is False and "slot04_drift" in res.failed_conditions