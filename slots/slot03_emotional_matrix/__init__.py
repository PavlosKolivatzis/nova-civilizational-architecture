# ruff: noqa: E402
"""Compatibility shim for nova.slots.slot03_emotional_matrix."""

from __future__ import annotations

from src_bootstrap import ensure_src_on_path

ensure_src_on_path()

import importlib
import sys

_target = "nova.slots.slot03_emotional_matrix"
_module = importlib.import_module(_target)

sys.modules.setdefault(_target, _module)
sys.modules[__name__] = _module
