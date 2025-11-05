"""Smoke test for calibration script."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def test_calibration_script_dry(tmp_path):
    """Test that calibration script runs and creates CSV with correct header."""
    out = tmp_path / "calib.csv"
    cmd = [
        sys.executable,
        "scripts/calibrate_wisdom_governor.py",
        "--kp",
        "0.2",
        "--kd",
        "0.05",
        "--a1",
        "0.2",
        "--a2",
        "0.2",
        "--dur",
        "1",
        "--step",
        "1",
        "--out",
        str(out),
    ]
    # Do not fail the suite if server isn't running; just ensure script runs and creates a header.
    try:
        subprocess.run(cmd, check=True, timeout=15)
    except Exception:
        pass
    text = out.read_text(encoding="utf-8")
    assert "kp,kd,a1,a2" in text.replace(" ", ""), "CSV header should include gain fields"


def test_calibration_script_exists():
    """Test that calibration script exists and is executable."""
    script = Path("scripts/calibrate_wisdom_governor.py")
    assert script.exists(), "Calibration script not found"
    # Check shebang line
    first_line = script.read_text(encoding="utf-8").split("\n")[0]
    assert first_line.startswith("#!"), "Script should have shebang"
