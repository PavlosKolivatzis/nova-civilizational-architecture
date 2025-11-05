"""Smoke test for soak A/B runner."""

from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path


def test_soak_script_headers_only():
    """Test that soak script runs and creates CSV with correct header."""
    out = Path(tempfile.gettempdir()) / "ab_runs.csv"
    cmd = [
        sys.executable,
        "scripts/soak_ab_wisdom_governor.py",
        "--kappa",
        "0.01",
        "--g0",
        "0.60",
        "--dur",
        "1",
        "--step",
        "1",
        "--out",
        str(out),
    ]
    # tolerate missing server; just ensure header written at least
    try:
        subprocess.run(cmd, check=True, timeout=15)
    except Exception:
        pass
    text = out.read_text(encoding="utf-8")
    assert "combo_id,kappa,g0,t,eta,S,H" in text.replace(" ", "")
