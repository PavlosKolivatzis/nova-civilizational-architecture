"""Smoke test for A/B runs summarizer."""

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
def test_summary_script_creates_md(tmp_path):
    """Test that summarizer creates Markdown table from CSV."""
    csv = tmp_path / "runs.csv"
    md = tmp_path / "report.md"
    pd.DataFrame(
        {
            "kappa": [0.01, 0.02],
            "g0": [0.6, 0.65],
            "S": [0.04, 0.02],
            "H": [0.03, 0.01],
            "bias": [0.005, 0.02],
            "Gstar": [0.7, 0.55],
            "clamp": [0.05, 0.12],
            "eta": [0.1, 0.09],
        }
    ).to_csv(csv, index=False)
    subprocess.run(
        [
            sys.executable,
            "scripts/summarize_wisdom_ab_runs.py",
            "--csv",
            str(csv),
            "--out",
            str(md),
        ],
        check=True,
    )
    assert "κ" in md.read_text(encoding="utf-8")
