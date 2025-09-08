# -*- coding: utf-8 -*-
"""Adapter registry for contract-based routing.

Exports AdapterRegistry and (when present) the concrete slot adapters so
legacy imports from orchestrator.app/tests continue to work.
"""

from __future__ import annotations
from importlib import import_module
from typing import List

from .registry import AdapterRegistry  # always exported

__all__: List[str] = ["AdapterRegistry"]

# best effort re-exports for backward compatibility
# (skip silently if an optional adapter module is missing)
_ADAPTER_MODULES = [
    "slot1_truth_anchor",
    "slot2_deltathresh",
    "slot3_emotional",
    "slot4_tri",
    "slot5_constellation",
    "slot6_cultural",
    "slot7_production_controls",
    "slot8_memory_ethics",
    "slot9_distortion_protection",
    "slot10_civilizational",
]

for modname in _ADAPTER_MODULES:
    try:
        mod = import_module(f".{modname}", __package__)
        # export every symbol that endswith 'Adapter' from the module
        for k, v in vars(mod).items():
            if k.endswith("Adapter"):
                globals()[k] = v  # type: ignore[assignment]
                __all__.append(k)
    except Exception:
        # adapter is optional or not present in this build – ignore
        continue
