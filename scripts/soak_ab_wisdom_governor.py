#!/usr/bin/env python3
"""
Run A/B soaks over (kappa, g0) pairs and sample wisdom metrics from /metrics.

Two modes:
  (A) Manual restart per combo (default): script logs desired (kappa,g0) and scrapes metrics.
      Operator/service must apply env vars and restart.
  (B) Managed restart (optional): provide --restart-cmd '...' template; script will invoke it with
      KAPPA and G0 substituted (e.g., 'pwsh -Command "$env:NOVA_WISDOM_G_KAPPA=''{{KAPPA}}''; ...; Stop-Process ...; python -m uvicorn ..."').

CSV schema:
ts_utc, combo_id, kappa, g0, t, eta, S, H, rho, Gstar, bias, clamp, tri_C, eta_cap, slot7_jobs
"""

from __future__ import annotations

import argparse
import csv
import os
import re
import subprocess
import time
import urllib.request
from datetime import datetime

NAMES = [
    "nova_wisdom_eta_current",
    "nova_wisdom_stability_margin",
    "nova_wisdom_hopf_distance",
    "nova_wisdom_spectral_radius",
    "nova_wisdom_generativity",
    "nova_wisdom_eta_bias_from_generativity",
    "nova_tri_coherence",
    "nova_tri_eta_cap",
    "nova_slot07_max_jobs",
]


def scrape(url: str, timeout=3.0):
    try:
        with urllib.request.urlopen(url, timeout=timeout) as r:
            text = r.read().decode("utf-8", errors="ignore")
    except Exception:
        return {}
    vals = {}
    for name in NAMES:
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


def maybe_restart(cmd_tmpl: str | None, kappa: float, g0: float):
    if not cmd_tmpl:
        return
    cmd = cmd_tmpl.replace("{{KAPPA}}", str(kappa)).replace("{{G0}}", str(g0))
    # shell=True for cross-platform one-liner convenience; template under your control
    subprocess.run(cmd, shell=True, check=False)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--host", default="127.0.0.1")
    ap.add_argument("--port", type=int, default=8100)
    ap.add_argument("--dur", type=int, default=1800, help="seconds per combo (default 30m)")
    ap.add_argument("--step", type=int, default=5, help="scrape period in seconds")
    ap.add_argument("--kappa", type=float, nargs="+", required=True)
    ap.add_argument("--g0", type=float, nargs="+", required=True)
    ap.add_argument("--out", default=".artifacts/wisdom_ab_runs.csv")
    ap.add_argument(
        "--restart-cmd",
        default=None,
        help="Optional restart template; supports {{KAPPA}} and {{G0}} substitution",
    )
    args = ap.parse_args()

    url = f"http://{args.host}:{args.port}/metrics"
    os.makedirs(os.path.dirname(args.out) or ".", exist_ok=True)

    with open(args.out, "a", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        if f.tell() == 0:
            w.writerow(
                [
                    "ts_utc",
                    "combo_id",
                    "kappa",
                    "g0",
                    "t",
                    "eta",
                    "S",
                    "H",
                    "rho",
                    "Gstar",
                    "bias",
                    "clamp",
                    "tri_C",
                    "eta_cap",
                    "slot7_jobs",
                ]
            )

        combo_id = 0
        for kappa in args.kappa:
            for g0 in args.g0:
                combo_id += 1
                maybe_restart(args.restart_cmd, kappa, g0)
                t0 = time.time()
                while True:
                    t = int(time.time() - t0)
                    vals = scrape(url)
                    row = [
                        datetime.utcnow().isoformat(timespec="seconds") + "Z",
                        combo_id,
                        kappa,
                        g0,
                        t,
                        vals.get("nova_wisdom_eta_current"),
                        vals.get("nova_wisdom_stability_margin"),
                        vals.get("nova_wisdom_hopf_distance"),
                        vals.get("nova_wisdom_spectral_radius"),
                        vals.get("nova_wisdom_generativity"),
                        vals.get("nova_wisdom_eta_bias_from_generativity"),
                        1.0 if (vals.get("nova_wisdom_eta_current", 1.0) <= 0.051) else 0.0,
                        vals.get("nova_tri_coherence"),
                        vals.get("nova_tri_eta_cap"),
                        vals.get("nova_slot07_max_jobs"),
                    ]
                    w.writerow(row)
                    f.flush()
                    if t >= args.dur:
                        break
                    time.sleep(max(1, args.step))


if __name__ == "__main__":
    main()
