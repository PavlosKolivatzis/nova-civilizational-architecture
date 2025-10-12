"""Slot 8 Memory Lock & IDS Protection - Processual (4.0) Self-Healing System."""

__version__ = "4.0.0"
__maturity__ = "Processual"

from .core.types import (
    ThreatLevel,
    RepairAction,
    QuarantineReason,
    HealthMetrics,
    IDSEvent,
    SnapshotMeta,
    RepairDecision
)

from .core.policy import Slot8Policy
from .core.quarantine import QuarantineSystem
from .core.repair_planner import RepairPlanner
from .core.entropy_monitor import EntropyMonitor

__all__ = [
    "ThreatLevel",
    "RepairAction",
    "QuarantineReason",
    "HealthMetrics",
    "IDSEvent",
    "SnapshotMeta",
    "RepairDecision",
    "Slot8Policy",
    "QuarantineSystem",
    "RepairPlanner",
    "EntropyMonitor"
]