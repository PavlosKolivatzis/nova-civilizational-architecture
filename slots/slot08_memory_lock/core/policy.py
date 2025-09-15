"""Policy configuration for Slot 8 self-healing memory system."""

from dataclasses import dataclass
from typing import List, Dict, Any


@dataclass
class Slot8Policy:
    """Configuration policy for Processual-level memory protection."""

    # Snapshot management
    retention_snapshots: int = 32
    snapshot_interval_s: int = 60
    max_snapshot_age_s: int = 3600  # 1 hour

    # Performance budgets
    cpu_budget_pct: float = 0.02  # 2% CPU limit
    memory_budget_mb: int = 150   # 150MB for 10k objects
    scan_interval_s: int = 30

    # Recovery parameters
    max_repair_attempts: int = 3
    repair_timeout_s: int = 30
    quarantine_timeout_s: int = 300  # 5 minutes
    quarantine_flip_max_s: float = 1.0  # Max time for quarantine activation
    mttr_target_s: float = 5.0  # Mean Time To Recovery
    snapshot_timeout_s: int = 10  # Max time for snapshot creation
    verification_timeout_s: int = 2  # Max time for verification

    # IDS thresholds
    surge_threshold: int = 500  # writes per window
    surge_window_s: int = 60
    entropy_threshold: float = 0.8  # Schema churn rate
    forbidden_paths: List[str] = None

    # Cryptographic
    signer_key_ref: str = "ed25519://slot8-signing"  # KMS/HSM ref in prod
    signature_algorithm: str = "ed25519"

    # Integrity monitoring
    integrity_check_interval_s: int = 120
    corruption_tolerance: float = 0.0  # Zero tolerance
    tamper_detection_enabled: bool = True

    # Adaptive behavior
    adaptive_thresholds: bool = True
    learning_rate: float = 0.1
    confidence_threshold: float = 0.7

    def __post_init__(self):
        """Initialize default values for mutable fields."""
        if self.forbidden_paths is None:
            self.forbidden_paths = [
                "/etc/.*",
                "/var/lib/nova/secrets/.*",
                "/root/.*",
                r".*\.key",
                r".*\.pem",
                r".*\.p12"
            ]

    @property
    def quarantine_policy(self) -> 'QuarantinePolicy':
        """Get quarantine policy configuration."""
        return QuarantinePolicy(
            auto_quarantine_on_corruption=True,
            auto_quarantine_on_tamper=True,
            auto_quarantine_on_surge=True,
            allow_read_only_access=True,
            block_all_writes=True,
            alert_administrators=True,
            require_manual_approval=False,
            auto_recovery_after_s=self.quarantine_timeout_s,
            max_auto_recoveries=3,
            escalate_after_failures=2
        )


@dataclass
class AdaptiveThresholds:
    """Dynamic thresholds that adapt based on system behavior."""

    # Current adaptive values
    current_surge_threshold: int
    current_entropy_threshold: float
    current_scan_interval_s: int

    # Adaptation tracking
    adaptation_count: int = 0
    last_adaptation_ts: int = 0
    performance_history: List[float] = None

    # Bounds for safety
    min_surge_threshold: int = 100
    max_surge_threshold: int = 2000
    min_entropy_threshold: float = 0.3
    max_entropy_threshold: float = 0.95
    min_scan_interval_s: int = 10
    max_scan_interval_s: int = 300

    def __post_init__(self):
        """Initialize performance history."""
        if self.performance_history is None:
            self.performance_history = []


@dataclass
class QuarantinePolicy:
    """Policy for quarantine behavior during security incidents."""

    # Quarantine triggers
    auto_quarantine_on_corruption: bool = True
    auto_quarantine_on_tamper: bool = True
    auto_quarantine_on_surge: bool = True

    # Quarantine behavior
    allow_read_only_access: bool = True
    block_all_writes: bool = True
    alert_administrators: bool = True

    # Recovery from quarantine
    require_manual_approval: bool = False
    auto_recovery_after_s: int = 300
    max_auto_recoveries: int = 3

    # Escalation
    escalate_after_failures: int = 2
    escalation_targets: List[str] = None

    def __post_init__(self):
        """Initialize escalation targets."""
        if self.escalation_targets is None:
            self.escalation_targets = [
                "slot07_production_controls",
                "slot03_emotional_matrix"  # For threat escalation
            ]


def get_default_policy() -> Slot8Policy:
    """Get default policy configuration for Slot 8."""
    return Slot8Policy()


def get_production_policy() -> Slot8Policy:
    """Get production-hardened policy configuration."""
    return Slot8Policy(
        retention_snapshots=64,
        snapshot_interval_s=30,
        cpu_budget_pct=0.015,  # Tighter CPU budget
        max_repair_attempts=5,
        quarantine_timeout_s=600,  # Longer quarantine
        surge_threshold=250,  # More sensitive
        corruption_tolerance=0.0,  # Absolute zero tolerance
        adaptive_thresholds=True,
        tamper_detection_enabled=True
    )


def get_development_policy() -> Slot8Policy:
    """Get development-friendly policy configuration."""
    return Slot8Policy(
        retention_snapshots=16,
        snapshot_interval_s=120,
        cpu_budget_pct=0.05,  # More relaxed
        max_repair_attempts=2,
        quarantine_timeout_s=60,  # Shorter quarantine
        surge_threshold=1000,  # Less sensitive
        signer_key_ref="dev://slot8-dev-key",
        tamper_detection_enabled=True
    )