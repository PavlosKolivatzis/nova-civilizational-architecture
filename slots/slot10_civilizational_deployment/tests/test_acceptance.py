from __future__ import annotations
import re
from slots.slot10_civilizational_deployment.core import (
    Slot10Policy, Gatekeeper, CanaryController, MockHealthFeed, CanaryMetricsExporter, SnapshotBackout
)

def test_acceptance_canary_metrics_and_rollback(tmp_path):
    policy = Slot10Policy(min_stage_duration_s=0, rollback_timeout_s=10.0)
    feed = MockHealthFeed()
    gk = Gatekeeper(policy, feed)
    metrics = CanaryMetricsExporter(export_interval_s=0.0)
    ctrl = CanaryController(policy, gk, feed, metrics_exporter=metrics)
    backout = SnapshotBackout(policy)

    ctrl.start_deployment({"error_rate": 0.01, "latency_p95": 100.0, "saturation": 0.30})
    backout.record_promotion(
        slot10_id="app_accept",
        slot08_id="mem_accept",
        slot04_id="tri_accept",
        reason="acceptance"
    )

    # Healthy tick then breach by error rate
    ctrl.tick()
    feed.update_runtime(error_rate=0.03)
    breach = ctrl.tick()
    assert breach.action == "rollback"

    # Rollback performs within MTTR envelope
    rb = backout.rollback(lambda s: True, lambda s: True, lambda s: True)
    assert rb.success is True
    assert rb.execution_time_s <= policy.rollback_timeout_s

    # Export one metrics snapshot and verify key series present
    snap = metrics.capture_canary_state(ctrl)
    prom = metrics.get_prometheus_metrics(snap)
    for must in ("slot10_deploy_stage_pct", "slot10_deploy_active", "slot10_gate_status",
                 "slot10_slo_violations", "slot10_latency_p95_ms", "slot10_rollback_triggered"):
        assert re.search(rf"^{must}\b", prom, flags=re.M), f"missing metric: {must}"