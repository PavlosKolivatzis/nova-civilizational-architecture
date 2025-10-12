"""Policy configuration for Slot 10 Civilizational Deployment system."""

from dataclasses import dataclass
from typing import List


@dataclass
class Slot10Policy:
    """Configuration policy for Processual-level deployment automation."""

    # MTTR and performance SLOs
    mttr_target_s: float = 5.0  # Mean Time To Recovery
    canary_stage_timeout_s: int = 180  # Max time per canary stage
    rollback_timeout_s: float = 10.0  # Max time for rollback execution

    # Canary progression stages
    canary_stages: List[float] = None  # Will be set in __post_init__
    min_stage_duration_s: int = 300  # Minimum observation time per stage (5 minutes)
    # Minimum time between promotions (seconds). 0 disables the velocity guard.
    min_promotion_gap_s: float = 0.0

    # Canary invariants and safety limits
    max_stage_rollback_velocity_per_hour: int = 6  # Max one stage promotion per 10 minutes
    frozen_baseline_window_s: int = 300  # 5 minutes of stable metrics before canary

    # Gate thresholds (matching ACL registry gates)
    slot08_integrity_threshold: float = 0.7
    slot08_recovery_rate_threshold: float = 0.8
    slot04_drift_z_threshold: float = 3.0

    # Slot 10 golden signals SLOs (tightened for production)
    error_rate_multiplier: float = 1.15  # Allow 15% increase from baseline
    latency_p95_multiplier: float = 1.10  # Allow 10% latency increase
    saturation_threshold: float = 0.80  # 80% resource utilization limit

    # Cross-slot snapshot coordination
    snapshot_consistency_timeout_s: float = 30.0
    max_concurrent_rollbacks: int = 1  # Conservative rollback concurrency

    # Chaos and resilience testing
    chaos_scenarios: List[str] = None  # Will be set in __post_init__
    acceptable_chaos_recovery_rate: float = 0.8  # 80% auto-recovery success

    # Observability and alerting
    metrics_collection_interval_s: int = 30
    alert_cooldown_s: int = 300  # 5 minutes between similar alerts

    def __post_init__(self):
        """Initialize default values for mutable fields."""
        if self.canary_stages is None:
            self.canary_stages = [0.01, 0.05, 0.25, 0.50, 1.00]  # 1% → 100%

        if self.chaos_scenarios is None:
            self.chaos_scenarios = [
                "write_surge",
                "model_drift_spike",
                "partial_network_partition",
                "disk_full",
                "slow_io"
            ]

    @property
    def stage_count(self) -> int:
        """Number of canary stages."""
        return len(self.canary_stages)

    @property
    def total_canary_duration_s(self) -> int:
        """Total time for full canary rollout."""
        return self.stage_count * self.canary_stage_timeout_s