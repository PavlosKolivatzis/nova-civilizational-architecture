# ruff: noqa: E402
from ._shim_warning import warn_shim_use
"""Compatibility shim for nova.slots.slot10_civilizational_deployment."""

from __future__ import annotations

from src_bootstrap import ensure_src_on_path

ensure_src_on_path()
warn_shim_use("slot10_civilizational_deployment")


import importlib
import sys

_target = "nova.slots.slot10_civilizational_deployment"
_module = importlib.import_module(_target)

sys.modules.setdefault(_target, _module)
sys.modules[__name__] = _module
