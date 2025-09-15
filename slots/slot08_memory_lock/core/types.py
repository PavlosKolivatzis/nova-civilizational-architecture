"""Core types for Slot 8 Memory Lock & IDS self-healing system."""

from dataclasses import dataclass
from typing import Literal, Dict, Any, Optional
from enum import Enum


class SnapshotStatus(Enum):
    """Status of memory snapshots."""
    OK = "OK"
    QUARANTINED = "QUARANTINED"
    RESTORED = "RESTORED"
    FAILED = "FAILED"


class RepairAction(Enum):
    """Available repair actions for corruption recovery."""
    RESTORE_LAST_GOOD = "RESTORE_LAST_GOOD"
    MAJORITY_VOTE = "MAJORITY_VOTE"
    SEMANTIC_PATCH = "SEMANTIC_PATCH"
    BLOCK = "BLOCK"


class ThreatLevel(Enum):
    """IDS threat classification levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class QuarantineReason(Enum):
    """Reasons for quarantine activation."""
    CORRUPTION_DETECTED = "corruption_detected"
    TAMPER_EVIDENCE = "tamper_evidence"
    WRITE_SURGE = "write_surge"
    FORBIDDEN_ACCESS = "forbidden_access"
    REPLAY_ATTACK = "replay_attack"
    MANUAL_ACTIVATION = "manual_activation"
    INTEGRITY_FAILURE = "integrity_failure"


@dataclass
class SnapshotMeta:
    """Metadata for signed memory snapshots."""
    id: str
    parent_id: Optional[str]
    ts_ms: int
    merkle_root: str
    signer: str
    sig: str  # hex-encoded signature for consistency
    status: SnapshotStatus = SnapshotStatus.OK
    content_size: int = 0
    file_count: int = 0


@dataclass
class RepairDecision:
    """Decision output from repair planner."""
    action: RepairAction
    reason: str
    details: Dict[str, Any]
    confidence: float = 0.0
    estimated_time_s: float = 0.0


@dataclass
class IDSEvent:
    """Intrusion detection system event record."""
    event_type: str
    threat_level: ThreatLevel
    source_path: str
    description: str
    ts_ms: int
    metadata: Dict[str, Any]
    signature: Optional[bytes] = None


@dataclass
class HealthMetrics:
    """Memory system health indicators."""
    integrity_score: float  # 0.0-1.0, higher is better
    corruption_detected: bool
    tamper_evidence: bool
    checksum_mismatch: bool
    semantic_inversion: bool
    entropy_score: float  # Schema churn rate
    last_snapshot_age_s: float
    repair_attempts: int
    quarantine_active: bool


@dataclass
class PerformanceMetrics:
    """Performance tracking for overhead monitoring."""
    cpu_usage_pct: float
    memory_usage_mb: float
    snapshot_duration_s: float
    repair_duration_s: float
    total_operations: int
    successful_repairs: int
    failed_repairs: int