"""Core components for Slot 4 TRI Engine Processual capabilities."""

from __future__ import annotations
import importlib
from typing import TYPE_CHECKING

__version__ = "0.1.0"

# Public API (unchanged)
__all__ = (
    "TriEngine",
    "TriMetrics",
    "TriPolicy",
    "Health",
    "RepairDecision",
    "RepairAction",
    "DriftDetector",
    "SurgeDetector",
    "RepairPlanner",
    "TriSnapshotter",
    "SnapshotMeta",
    "SafeMode",
)

# Type-checkers see real symbols; runtime stays lazy
if TYPE_CHECKING:
    from .tri_engine import TriEngine, TriMetrics
    from .policy import TriPolicy
    from .types import Health, RepairDecision, RepairAction
    from .detectors import DriftDetector, SurgeDetector
    from .repair_planner import RepairPlanner
    from .snapshotter import TriSnapshotter, SnapshotMeta
    from .safe_mode import SafeMode

_LAZY_MAP = {
    "TriEngine": (".tri_engine", "TriEngine"),
    "TriMetrics": (".tri_engine", "TriMetrics"),
    "TriPolicy": (".policy", "TriPolicy"),
    "Health": (".types", "Health"),
    "RepairDecision": (".types", "RepairDecision"),
    "RepairAction": (".types", "RepairAction"),
    "DriftDetector": (".detectors", "DriftDetector"),
    "SurgeDetector": (".detectors", "SurgeDetector"),
    "RepairPlanner": (".repair_planner", "RepairPlanner"),
    "TriSnapshotter": (".snapshotter", "TriSnapshotter"),
    "SnapshotMeta": (".snapshotter", "SnapshotMeta"),
    "SafeMode": (".safe_mode", "SafeMode"),
}

def __getattr__(name: str):
    try:
        mod_name, attr = _LAZY_MAP[name]
    except KeyError as e:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}") from e
    mod = importlib.import_module(mod_name, __package__)
    obj = getattr(mod, attr)
    globals()[name] = obj  # cache for subsequent access
    return obj

def __dir__():
    return sorted(list(globals().keys()) + list(__all__))
