"""Core components for Slot 10 Processual deployment."""

from .policy import Slot10Policy
from .gatekeeper import Gatekeeper, GateResult
from .canary import CanaryController, CanaryResult, CanaryStage
from .snapshot_backout import SnapshotBackout, SnapshotSet, RollbackResult
from .health_feed import (
    HealthFeedAdapter, MockHealthFeed, LiveHealthFeed,
    Slot8Health, Slot4Health, RuntimeMetrics,
)
from .audit import AuditLog, AuditRecord, AuditSigner
from .metrics import CanaryMetrics, CanaryMetricsExporter
from .lightclock_gatekeeper import LightClockGatekeeper, LightClockGateResult
from .lightclock_canary import LightClockCanaryController, LightClockCanaryResult
from .factory import build_canary_controller, get_lightclock_gate_summary

__all__ = [
    "Slot10Policy",
    "Gatekeeper", "GateResult",
    "CanaryController", "CanaryResult", "CanaryStage",
    "SnapshotBackout", "SnapshotSet", "RollbackResult",
    "HealthFeedAdapter", "MockHealthFeed", "LiveHealthFeed",
    "Slot8Health", "Slot4Health", "RuntimeMetrics",
    "AuditLog", "AuditRecord", "AuditSigner",
    "CanaryMetrics", "CanaryMetricsExporter",
    "LightClockGatekeeper", "LightClockGateResult",
    "LightClockCanaryController", "LightClockCanaryResult",
    "build_canary_controller", "get_lightclock_gate_summary",
]