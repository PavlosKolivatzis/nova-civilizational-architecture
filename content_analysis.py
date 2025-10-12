# ruff: noqa: E402
"""Compatibility shim for nova.content_analysis."""

from __future__ import annotations

from src_bootstrap import ensure_src_on_path

ensure_src_on_path()

from nova.content_analysis import *  # noqa: F401,F403
