#!/usr/bin/env python3
"""Compatibility wrapper for CI runners expecting verify_pilot_ready.py at repo root."""

from scripts.verify_pilot_ready import main


if __name__ == "__main__":
    raise SystemExit(main())
