from __future__ import annotations
from slots.slot10_civilizational_deployment.core import Slot10Policy, Gatekeeper
from slots.slot10_civilizational_deployment.core import CanaryController

def s8_ok():
    return {"integrity_score": 0.95, "quarantine_active": False, "recent_recoveries": {"success_rate_5m": 0.95}}

def s4_ok():
    return {"safe_mode_active": False, "drift_z": 0.5}

def baseline():
    return {"error_rate": 0.01, "latency_p95": 100.0, "saturation": 0.30}

def current_green():
    return {"error_rate": 0.01, "latency_p95": 100.0, "saturation": 0.50}

def current_bad():
    # error rate breaches multiplier (2x vs 1.2x allowed)
    return {"error_rate": 0.02, "latency_p95": 100.0, "saturation": 0.50}

def test_canary_promotes_when_all_green():
    policy = Slot10Policy(min_stage_duration_s=0)  # no waiting in tests
    gk = Gatekeeper(policy)
    ctrl = CanaryController(policy, gk)
    ctrl.start_deployment(baseline())
    out = None
    # advance through all stages deterministically
    for _ in range(policy.stage_count):
        out = ctrl.evaluate_stage(current_green(), s8_ok(), s4_ok())
        assert out.action in ("continue", "promote")
        if out.action == "promote" and out.stage_idx == policy.stage_count - 1:
            break
    assert out and out.action == "promote"

def test_canary_rolls_back_on_slo_violation():
    policy = Slot10Policy(min_stage_duration_s=0)
    gk = Gatekeeper(policy)
    ctrl = CanaryController(policy, gk)
    ctrl.start_deployment(baseline())
    out = ctrl.evaluate_stage(current_bad(), s8_ok(), s4_ok())
    assert out.action == "rollback"