"""Core components for Slot 8 self-healing memory protection."""

from .types import (
    ThreatLevel,
    RepairAction,
    QuarantineReason,
    HealthMetrics,
    IDSEvent,
    SnapshotMeta,
    RepairDecision
)

from .policy import Slot8Policy, QuarantinePolicy
from .quarantine import QuarantineSystem
from .repair_planner import RepairPlanner
from .entropy_monitor import EntropyMonitor
from .integrity_store import MerkleIntegrityStore
from .snapshotter import IntegritySnapshotter

__all__ = [
    "ThreatLevel",
    "RepairAction",
    "QuarantineReason",
    "HealthMetrics",
    "IDSEvent",
    "SnapshotMeta",
    "RepairDecision",
    "Slot8Policy",
    "QuarantinePolicy",
    "QuarantineSystem",
    "RepairPlanner",
    "EntropyMonitor",
    "MerkleIntegrityStore",
    "IntegritySnapshotter"
]
