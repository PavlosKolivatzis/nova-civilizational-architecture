"""Smoke test for A/B runs plotting helper."""

from __future__ import annotations

import subprocess
import sys

import pytest

try:
    import pandas as pd

    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False


@pytest.mark.skipif(not PANDAS_AVAILABLE, reason="pandas not installed")
def test_plotter_outputs_pngs(tmp_path):
    """Test that plotting script generates PNG files."""
    csv = tmp_path / "runs.csv"
    md = tmp_path / "report.md"
    out = tmp_path / "imgs"

    # minimal fake dataset for 2 combos
    df = pd.DataFrame(
        {
            "kappa": [0.01] * 5 + [0.02] * 5,
            "g0": [0.60] * 5 + [0.65] * 5,
            "t": list(range(5)) + list(range(5)),
            "eta": [0.10, 0.11, 0.10, 0.09, 0.10] * 2,
            "S": [0.035, 0.034, 0.036, 0.033, 0.037] * 2,
            "H": [0.025] * 10,
            "rho": [0.9] * 10,
            "Gstar": [0.65, 0.66, 0.67, 0.66, 0.65] * 2,
            "bias": [0.005] * 10,
            "clamp": [0, 0, 0, 0, 0] * 2,
            "tri_C": [0.7] * 10,
            "eta_cap": [0.18] * 10,
            "slot7_jobs": [16] * 10,
        }
    )
    df.to_csv(csv, index=False)
    md.write_text(
        "| κ | G₀ | ... | Verdict |\n"
        "|---|----|---|---|\n"
        "| 0.01 | 0.60 | ... | ✅ PASS |\n"
        "| 0.02 | 0.65 | ... | ❌ FAIL |\n",
        encoding="utf-8",
    )

    subprocess.run(
        [
            sys.executable,
            "scripts/plot_wisdom_ab_runs.py",
            "--csv",
            str(csv),
            "--report",
            str(md),
            "--outdir",
            str(out),
        ],
        check=True,
    )

    files = list(out.glob("*.png"))
    assert len(files) >= 4
