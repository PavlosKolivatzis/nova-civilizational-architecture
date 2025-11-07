#!/usr/bin/env python3
"""
Summarize A/B soak runs (.artifacts/wisdom_ab_runs.csv)
-> outputs Markdown table + CSV summary for docs/reflections/phase_15_8_5_ab_report.md
"""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd


def _safe_print(text: str) -> None:
    """Print text but degrade to ASCII when console encoding cannot represent it."""
    try:
        print(text)
    except UnicodeEncodeError:
        encoded = text.encode("ascii", "replace").decode("ascii")
        print(encoded)


def summarize(csv_path: str, md_out: str):
    df = pd.read_csv(csv_path)
    if df.empty:
        print("No data found.")
        return

    # aggregate per (kappa,g0)
    agg = df.groupby(["kappa", "g0"]).agg(
        S_mean=("S", "mean"),
        H_min=("H", "min"),
        bias_abs_mean=("bias", lambda s: s.abs().mean()),
        G_mean=("Gstar", "mean"),
        G_std=("Gstar", "std"),
        clamp_ratio=("clamp", "mean"),
        eta_p95=("eta", lambda s: np.nanpercentile(s.dropna(), 95)),
    ).reset_index()

    # success criteria
    ok = (
        (agg.S_mean >= 0.03)
        & (agg.H_min >= 0.02)
        & (agg.bias_abs_mean <= 0.01)
        & (agg.G_mean >= 0.25)
        & (agg.G_std < 0.05)
        & (agg.clamp_ratio < 0.10)
    )
    agg["verdict"] = np.where(ok, "PASS", "FAIL")

    # Write Markdown
    md_table = "| κ | G₀ | S_mean | H_min | |Δη|_mean | G*_mean | σ(G*) | clamp_ratio | η_p95 | Verdict |\n"
    md_table += "|---|----|--------|-------|-----------|---------|--------|-------------|--------|---------|\n"
    for _, r in agg.iterrows():
        md_table += (
            f"| {r.kappa:.2f} | {r.g0:.2f} | {r.S_mean:.3f} | {r.H_min:.3f} | "
            f"{r.bias_abs_mean:.3f} | {r.G_mean:.3f} | {r.G_std:.3f} | "
            f"{r.clamp_ratio:.2f} | {r.eta_p95:.3f} | {r.verdict} |\n"
        )

    out_path = Path(md_out)
    text = out_path.read_text(encoding="utf-8") if out_path.exists() else ""
    text = (
        text.split("## Results", 1)[0]
        + "## Results\n\n"
        + md_table
        + "\n"
        + "## Recommendation\n\n(Select winner based on PASS rows)\n"
    )
    out_path.write_text(text, encoding="utf-8")

    print(f"[ok] Summary written to {md_out}")
    _safe_print(md_table)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--csv", default=".artifacts/wisdom_ab_runs.csv")
    ap.add_argument("--out", default="docs/reflections/phase_15_8_5_ab_report.md")
    args = ap.parse_args()
    summarize(args.csv, args.out)


if __name__ == "__main__":
    main()
