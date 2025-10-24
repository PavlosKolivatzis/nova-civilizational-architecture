"""Slot registry helpers for alignment checks."""

from __future__ import annotations

from importlib import import_module
from typing import Dict

from nova.slot_loader import load_slot

SLOT_IDS = [
    "slot01_truth_anchor",
    "slot02_deltathresh",
    "slot03_emotional_matrix",
    "slot04_tri",
    "slot05_constellation",
    "slot06_cultural_synthesis",
    "slot07_production_controls",
    "slot08_memory_lock",
    "slot08_memory_ethics",
    "slot09_distortion_protection",
    "slot10_civilizational_deployment",
]


def list_ids() -> list[str]:
    """Return the canonical slot identifiers."""
    return list(SLOT_IDS)


def ensure_loaded() -> Dict[str, object]:
    """Import every slot module and return the module mapping."""
    modules: Dict[str, object] = {}
    for slot in SLOT_IDS:
        modules[slot] = load_slot(slot)
    return modules


def load(slot_id: str):
    """Load a slot module by id (thin wrapper for consumers)."""
    if slot_id not in SLOT_IDS:
        raise KeyError(f"Unknown slot id: {slot_id}")
    return load_slot(slot_id)
