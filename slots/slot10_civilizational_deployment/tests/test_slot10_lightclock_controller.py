from slots.slot10_civilizational_deployment.core.lightclock_canary import LightClockCanaryController
from slots.slot10_civilizational_deployment.core.lightclock_gatekeeper import LightClockGatekeeper
from types import SimpleNamespace

class DummyHealth:
    def __init__(self, mirror):
        self.mirror = mirror
    def get_slot8_health(self):
        return SimpleNamespace(
            integrity_score=1.0,
            quarantine_active=False,
            recent_recoveries=0,
        )
    def get_slot4_health(self):
        return SimpleNamespace(safe_mode_active=False, drift_z=0.0)
    def get_runtime_metrics(self):
        return SimpleNamespace(error_rate=0.0, latency_p95=100, saturation=0.3)

class DummyPolicy:
    min_promotion_gap_s=30
    min_stage_duration_s=60
    canary_stage_timeout_s=600
    error_rate_multiplier=1.2
    latency_p95_multiplier=1.2
    saturation_threshold=0.9
    canary_stages=[0.01, 0.05, 0.25, 1.0]

def test_lightclock_controller_tick_promotes(monkeypatch):
    mirror = type("M",(object,),{"read":lambda self,k,d=None: {"slot07.phase_lock":0.9,"slot09.final_policy":"ALLOW_FASTPATH","slot04.tri_score":0.8}.get(k,d)})()
    ctl = LightClockCanaryController(
        policy=DummyPolicy(),
        lightclock_gatekeeper=LightClockGatekeeper(mirror=mirror),
        health_feed=DummyHealth(mirror),
        audit=None,
        metrics_exporter=None
    )
    # minimal stages setup - stage with sufficient duration to pass promotion
    ctl.stages = [type("Stage",(object,),{"duration":120,"slo_violations":0, "start_time": None, "end_time": None})()]
    ctl.current_stage_idx = 0
    ctl._last_promotion_ts = None
    ctl.baseline_metrics = {"error_rate": 0.0, "latency_p95": 100, "saturation": 0.3}
    ctl.frozen_baseline = ctl.baseline_metrics
    res = ctl.tick()
    assert res.success