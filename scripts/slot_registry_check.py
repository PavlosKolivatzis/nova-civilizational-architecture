#!/usr/bin/env python3
"""Phase-11 alignment smoke check for slot registration."""

from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src_bootstrap import ensure_src_on_path

REQUIRED_SLOTS = {
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
}


def main() -> int:
    ensure_src_on_path()
    try:
        from nova.slots import registry  # type: ignore
    except ImportError as exc:  # pragma: no cover - environment break glass
        print(f"Failed to import nova slot registry: {exc}")
        return 2

    discovered = set(registry.list_ids())
    missing = sorted(REQUIRED_SLOTS - discovered)
    unexpected = sorted(discovered - REQUIRED_SLOTS)

    if missing:
        print(f"Missing slots: {missing}")
        return 1
    if unexpected:
        print(f"Unexpected slots in registry: {unexpected}")
        return 1

    try:
        registry.ensure_loaded()
    except Exception as exc:  # pragma: no cover - defensive
        print(f"Slot import failed: {exc}")
        return 1

    print("Slots OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
