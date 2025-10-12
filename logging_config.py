# ruff: noqa: E402
"""Compatibility shim for nova.logging_config."""

from __future__ import annotations

from src_bootstrap import ensure_src_on_path

ensure_src_on_path()

from nova.logging_config import *  # noqa: F401,F403
