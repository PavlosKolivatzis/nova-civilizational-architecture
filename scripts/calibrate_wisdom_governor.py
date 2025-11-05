#!/usr/bin/env python3
"""
Calibrate Adaptive Wisdom Governor by sweeping KP/KD/a1/a2 and sampling Prometheus-exported gauges.

Usage (live metrics):
  python scripts/calibrate_wisdom_governor.py --host 127.0.0.1 --port 8100 \
      --dur 120 --step 5 --kp 0.2 0.4 --kd 0.05 0.1 --a1 0.2 --a2 0.2 \
      --out .artifacts/wisdom_calibration_15-8-3.csv

Optionally, synthetic step inputs (if your poller supports debug envs):
  --step-s "0:0.025,60:0.045" --step-tri "0:0.40,60:0.85"
"""

from __future__ import annotations

import argparse
import csv
import re
import time
import urllib.request
from datetime import datetime

METRICS = [
    "nova_wisdom_eta_current",
    "nova_wisdom_stability_margin",
    "nova_wisdom_hopf_distance",
    "nova_wisdom_spectral_radius",
    "nova_tri_coherence",
    "nova_tri_eta_cap",
    "nova_slot07_max_jobs",
]


def scrape_metrics(url: str) -> dict:
    """Scrape Prometheus metrics from /metrics endpoint."""
    try:
        with urllib.request.urlopen(url, timeout=2.5) as r:
            text = r.read().decode("utf-8", errors="ignore")
    except Exception:
        return {}
    vals = {}
    for name in METRICS:
        # match e.g. 'name 0.123' or 'name{...} 0.123' — take the first unlabeled total
        m = re.search(
            rf"^{name}(?:\{{[^}}]*\}})?\s+([+-]?\d+(?:\.\d+)?(?:e[+-]?\d+)?)$",
            text,
            flags=re.MULTILINE | re.IGNORECASE,
        )
        if m:
            try:
                vals[name] = float(m.group(1))
            except Exception:
                pass
    return vals


def iter_grid(kp_list, kd_list, a1_list, a2_list):
    """Iterate over all combinations of gain parameters."""
    for kp in kp_list:
        for kd in kd_list:
            for a1 in a1_list:
                for a2 in a2_list:
                    yield (kp, kd, a1, a2)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--host", default="127.0.0.1")
    p.add_argument("--port", type=int, default=8100)
    p.add_argument("--dur", type=int, default=120, help="seconds to sample per setting")
    p.add_argument("--step", type=int, default=5, help="sample period seconds")
    p.add_argument("--kp", type=float, nargs="+", required=True)
    p.add_argument("--kd", type=float, nargs="+", required=True)
    p.add_argument("--a1", type=float, nargs="+", required=True)
    p.add_argument("--a2", type=float, nargs="+", required=True)
    p.add_argument("--out", default=".artifacts/wisdom_calibration_15-8-3.csv")
    p.add_argument(
        "--step-s", default="", help="synthetic steps e.g. '0:0.025,60:0.045' (optional)"
    )
    p.add_argument(
        "--step-tri", default="", help="synthetic steps e.g. '0:0.40,60:0.85' (optional)"
    )
    args = p.parse_args()

    url = f"http://{args.host}:{args.port}/metrics"
    with open(args.out, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        header = [
            "ts",
            "kp",
            "kd",
            "a1",
            "a2",
            "t",
            "eta",
            "S",
            "H",
            "rho",
            "tri_C",
            "eta_cap",
            "slot7_jobs",
        ]
        w.writerow(header)

        for kp, kd, a1, a2 in iter_grid(args.kp, args.kd, args.a1, args.a2):
            # Set gains via env-aware control endpoint if available, else just annotate CSV.
            t0 = time.time()
            while True:
                t = int(time.time() - t0)
                vals = scrape_metrics(url)
                row = [
                    datetime.utcnow().isoformat(),
                    kp,
                    kd,
                    a1,
                    a2,
                    t,
                    vals.get("nova_wisdom_eta_current"),
                    vals.get("nova_wisdom_stability_margin"),
                    vals.get("nova_wisdom_hopf_distance"),
                    vals.get("nova_wisdom_spectral_radius"),
                    vals.get("nova_tri_coherence"),
                    vals.get("nova_tri_eta_cap"),
                    vals.get("nova_slot07_max_jobs"),
                ]
                w.writerow(row)
                f.flush()
                if t >= args.dur:
                    break
                time.sleep(max(1, args.step))
    print(f"Saved: {args.out}")


if __name__ == "__main__":
    main()
