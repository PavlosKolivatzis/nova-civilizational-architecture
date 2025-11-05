#!/usr/bin/env python3
"""
Plot A/B soak results → PNG charts.

Inputs:
  .artifacts/wisdom_ab_runs.csv  (from soak_ab_wisdom_governor.py)
  docs/reflections/phase_15_8_5_ab_report.md (optional, for PASS/FAIL coloring via summarize tool)

Outputs (docs/images/phase15-8-5/):
  - eta_trajectories.png          (η over time, one line per combo)
  - gstar_vs_S_scatter.png        (G* vs S_mean, colored by PASS/FAIL)
  - stability_boxplots.png        (S distribution grouped by (κ,G0))
  - clamp_ratio_heatmap.png       (heatmap κ×G0 of clamp ratio)

Note: uses matplotlib only.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


def _ensure_dir(p: Path):
    p.mkdir(parents=True, exist_ok=True)


def load_csv(csv_path: Path) -> pd.DataFrame:
    df = pd.read_csv(csv_path)
    # type hygiene
    for c in [
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
    ]:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce")
    return df


def load_pass_fail(md_report: Path) -> pd.DataFrame:
    if not md_report.exists():
        return pd.DataFrame()
    text = md_report.read_text(encoding="utf-8")
    # Parse table rows like: | 0.01 | 0.60 | ... | ✅ PASS |
    rows = []
    for line in text.splitlines():
        if not line.strip().startswith("|") or "Verdict" in line or "---" in line:
            continue
        cols = [c.strip() for c in line.strip("|").split("|")]
        if len(cols) < 10:
            continue
        try:
            kappa = float(cols[0])
            g0 = float(cols[1])
            verdict = cols[-1]
            rows.append({"kappa": kappa, "g0": g0, "verdict": verdict})
        except Exception:
            pass
    return pd.DataFrame(rows).drop_duplicates()


def plot_eta_trajectories(df: pd.DataFrame, out: Path):
    plt.figure(figsize=(10, 6))
    for (k, g), gdf in df.groupby(["kappa", "g0"]):
        gdf = gdf.sort_values("t")
        plt.plot(gdf["t"], gdf["eta"], label=f"κ={k:.2f}, G₀={g:.2f}", linewidth=1.1)
    plt.xlabel("time [s]")
    plt.ylabel("η (learning rate)")
    plt.title("η trajectories by (κ, G₀)")
    plt.legend(loc="best", fontsize=8)
    plt.tight_layout()
    plt.savefig(out, dpi=120)
    plt.close()


def plot_gstar_vs_S(df: pd.DataFrame, verdicts: pd.DataFrame, out: Path):
    agg = (
        df.groupby(["kappa", "g0"])
        .agg(S_mean=("S", "mean"), G_mean=("Gstar", "mean"))
        .reset_index()
    )
    if not verdicts.empty:
        agg = agg.merge(verdicts, on=["kappa", "g0"], how="left")
    colors = np.where(
        agg.get("verdict", "").astype(str).str.contains("PASS"), "tab:green", "tab:red"
    )
    plt.figure(figsize=(7, 6))
    plt.scatter(agg["S_mean"], agg["G_mean"], c=colors)
    for _, r in agg.iterrows():
        plt.annotate(
            f"κ={r.kappa:.2f},G₀={r.g0:.2f}",
            (r.S_mean, r.G_mean),
            fontsize=8,
            xytext=(3, 3),
            textcoords="offset points",
        )
    plt.axvline(0.03, linestyle="--", linewidth=1)
    plt.axhline(0.6, linestyle="--", linewidth=1)
    plt.xlabel("S_mean")
    plt.ylabel("G*_mean")
    plt.title("G* vs S_mean (PASS=green, FAIL=red)")
    plt.tight_layout()
    plt.savefig(out, dpi=140)
    plt.close()


def plot_stability_boxplots(df: pd.DataFrame, out: Path):
    # one box per (κ,G0)
    order = sorted(
        df[["kappa", "g0"]].drop_duplicates().itertuples(index=False),
        key=lambda x: (x.kappa, x.g0),
    )
    labels, data = [], []
    for k, g in order:
        series = df[(df["kappa"] == k) & (df["g0"] == g)]["S"].dropna()
        if len(series):
            labels.append(f"κ={k:.2f}\nG₀={g:.2f}")
            data.append(series.values)
    plt.figure(figsize=(max(8, len(labels) * 0.9), 6))
    plt.boxplot(data, labels=labels, vert=True, showfliers=False)
    plt.ylabel("S (stability margin)")
    plt.title("Stability margin distribution by (κ, G₀)")
    plt.tight_layout()
    plt.savefig(out, dpi=140)
    plt.close()


def plot_clamp_heatmap(df: pd.DataFrame, out: Path):
    agg = (
        df.groupby(["kappa", "g0"]).agg(clamp_ratio=("clamp", "mean")).reset_index()
    )
    piv = agg.pivot(index="kappa", columns="g0", values="clamp_ratio")
    plt.figure(figsize=(6, 5))
    im = plt.imshow(piv.values, aspect="auto", origin="lower")
    plt.colorbar(im, fraction=0.046, pad=0.04, label="clamp_ratio")
    plt.xticks(range(len(piv.columns)), [f"{c:.2f}" for c in piv.columns])
    plt.yticks(range(len(piv.index)), [f"{r:.2f}" for r in piv.index])
    plt.xlabel("G₀")
    plt.ylabel("κ")
    plt.title("Clamp ratio heatmap (κ × G₀)")
    plt.tight_layout()
    plt.savefig(out, dpi=140)
    plt.close()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--csv", default=".artifacts/wisdom_ab_runs.csv")
    ap.add_argument("--report", default="docs/reflections/phase_15_8_5_ab_report.md")
    ap.add_argument("--outdir", default="docs/images/phase15-8-5")
    args = ap.parse_args()

    outdir = Path(args.outdir)
    _ensure_dir(outdir)
    df = load_csv(Path(args.csv))
    if df.empty:
        print("No CSV rows found.")
        return
    verdicts = load_pass_fail(Path(args.report))

    plot_eta_trajectories(df, outdir / "eta_trajectories.png")
    plot_gstar_vs_S(df, verdicts, outdir / "gstar_vs_S_scatter.png")
    plot_stability_boxplots(df, outdir / "stability_boxplots.png")
    plot_clamp_heatmap(df, outdir / "clamp_ratio_heatmap.png")
    print(f"Charts saved to: {outdir}")


if __name__ == "__main__":
    main()
