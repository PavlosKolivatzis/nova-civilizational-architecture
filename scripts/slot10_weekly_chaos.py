#!/usr/bin/env python3
"""
Weekly chaos: Slot 10 canary → healthy ticks → inject breach → rollback → export metrics.
Safe no-op for prod unless invoked manually/CI.
"""
from __future__ import annotations
from pathlib import Path
import argparse
import json
import time
import random
from nova.slots.slot10_civilizational_deployment.core import (
    Slot10Policy, Gatekeeper, CanaryController,
    MockHealthFeed, CanaryMetricsExporter, SnapshotBackout
)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--export-dir", default="artifacts")
    ap.add_argument("--export-prom", default="slot10_metrics.prom")
    args = ap.parse_args()
    random.seed(args.seed)

    export_dir = Path(args.export_dir)
    export_dir.mkdir(parents=True, exist_ok=True)

    # Production-ish policy but with fast stage time so CI completes quickly
    policy = Slot10Policy(min_stage_duration_s=0, rollback_timeout_s=10.0)
    feed = MockHealthFeed()
    gk = Gatekeeper(policy, feed)
    metrics = CanaryMetricsExporter(export_interval_s=0.0)
    ctrl = CanaryController(policy, gk, feed, metrics_exporter=metrics)
    backout = SnapshotBackout(policy)

    baseline = {"error_rate": 0.01, "latency_p95": 100.0, "saturation": 0.30}
    start = ctrl.start_deployment(baseline)

    # Record a "promotion snapshot set" (stub ids for coordination)
    snap = backout.record_promotion(
        slot10_id=f"app_{int(time.time())}",
        slot08_id="mem_snap_weekly",
        slot04_id="tri_model_weekly",
        reason="weekly_chaos_canary"
    )

    # Healthy ticks (exercise green path)
    steps = []
    for i in range(2):
        r = ctrl.tick()
        steps.append({"step": f"green_{i}", "action": r.action, "reason": r.reason})

    # Inject deterministic breach: error rate beyond hardened multiplier
    feed.update_runtime(error_rate=0.03)  # baseline 0.01, policy=1.15x → threshold ~0.0115
    breach = ctrl.tick()
    steps.append({"step": "breach", "action": breach.action, "reason": breach.reason})

    # Perform coordinated rollback if requested
    rb = None
    if breach.action == "rollback":
        rb = backout.rollback(
            app_restore=lambda s: True,
            slot8_restore=lambda s: True,
            slot4_restore=lambda s: True,
        )

    # Export Prometheus metrics snapshot
    snap_metrics = metrics.capture_canary_state(ctrl)
    prom_text = metrics.get_prometheus_metrics(snap_metrics)
    (export_dir / args.export_prom).write_text(prom_text, encoding="utf-8")

    # JSON report (handy for dashboards)
    report = {
        "start": {"action": start.action, "reason": start.reason},
        "snapshot_set": {"slot10": snap.slot10_id, "slot08": snap.slot08_id, "slot04": snap.slot04_id, "reason": snap.reason},
        "steps": steps,
        "rollback": None if rb is None else {
            "success": rb.success,
            "elapsed_s": rb.execution_time_s,
            "slot10": rb.slot10_success, "slot08": rb.slot08_success, "slot04": rb.slot04_success,
            "errors": rb.errors,
        },
    }
    (export_dir / "slot10_weekly_chaos.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print("[weekly-chaos] complete ->", export_dir)

if __name__ == "__main__":
    main()