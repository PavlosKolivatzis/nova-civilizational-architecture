"""Legacy slots package augmented to include src/nova slots."""

from __future__ import annotations

import logging
import sys
from importlib import import_module
from pathlib import Path

from src_bootstrap import ensure_src_on_path

memory_logger = logging.getLogger("memory")

ensure_src_on_path()

_src_slots_dir = Path(__file__).resolve().parent.parent / "src" / "nova" / "slots"
if _src_slots_dir.exists():
    _src_slots_str = str(_src_slots_dir)
    if _src_slots_str not in __path__:
        __path__.append(_src_slots_str)

# Ensure the nova.slots namespace points to the same module when requested
try:
    nova_slots = import_module("nova.slots")
except ModuleNotFoundError:
    nova_slots = None
else:
    sys.modules.setdefault("nova.slots", sys.modules[__name__])
