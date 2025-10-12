# ruff: noqa: E402
"""Compatibility shim for nova.slots.slot08_memory_ethics."""

from __future__ import annotations

from pathlib import Path
from src_bootstrap import ensure_src_on_path

ensure_src_on_path()

import importlib
import sys

_target = "nova.slots.slot08_memory_ethics"
_module = importlib.import_module(_target)

src_path = Path(__file__).resolve().parents[2] / 'src' / 'nova' / 'slots' / 'slot08_memory_ethics'
root_path = Path(__file__).resolve().parent

__path__ = []
for candidate in (root_path, src_path):
    if candidate.exists():
        path_str = str(candidate)
        if path_str not in __path__:
            __path__.append(path_str)

if hasattr(_module, '__path__'):
    for entry in _module.__path__:
        if entry not in __path__:
            __path__.append(entry)

sys.modules.setdefault(_target, _module)
sys.modules[__name__] = _module
