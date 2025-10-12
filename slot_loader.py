# ruff: noqa: E402
"""Compatibility shim for nova.slot_loader."""

from __future__ import annotations

from src_bootstrap import ensure_src_on_path

ensure_src_on_path()

from nova.slot_loader import *  # noqa: F401,F403
