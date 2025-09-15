"""Core components for Slot 10 Processual deployment."""

from .policy import Slot10Policy
from .gatekeeper import Gatekeeper, GateResult
from .canary import CanaryController, CanaryResult, CanaryStage
from .snapshot_backout import SnapshotBackout, SnapshotSet, RollbackResult
from .health_feed import (
    HealthFeedAdapter, MockHealthFeed, LiveHealthFeed,
    Slot8Health, Slot4Health, RuntimeMetrics,
)

__all__ = [
    "Slot10Policy",
    "Gatekeeper", "GateResult",
    "CanaryController", "CanaryResult", "CanaryStage",
    "SnapshotBackout", "SnapshotSet", "RollbackResult",
    "HealthFeedAdapter", "MockHealthFeed", "LiveHealthFeed",
    "Slot8Health", "Slot4Health", "RuntimeMetrics",
]