# ruff: noqa: E402
"""Compatibility shim for nova.slots.slot07_production_controls."""

from __future__ import annotations

from ._shim_warning import warn_shim_use

from src_bootstrap import ensure_src_on_path

ensure_src_on_path()
warn_shim_use("slot07_production_controls")


import importlib
import sys

_target = "nova.slots.slot07_production_controls"
_module = importlib.import_module(_target)

sys.modules.setdefault(_target, _module)
sys.modules[__name__] = _module
