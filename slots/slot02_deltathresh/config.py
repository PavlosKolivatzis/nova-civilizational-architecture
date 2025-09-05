from enum import Enum
from dataclasses import dataclass, field
from typing import Dict

class OperationalMode(Enum):
    STABLE_LOCK = "stable_lock"
    CANARY_TIGHT = "canary_tight"
    PASS_THROUGH = "pass_through"

class ProcessingMode(Enum):
    QUARANTINE_ONLY = "quarantine_only"
    NEUTRALIZE_PATTERNS = "neutralize_patterns"
    HYBRID_PROCESSING = "hybrid_processing"


class QuarantineReasonCode(Enum):
    """Standardized reason codes for quarantine decisions."""

    TRI_BELOW_MIN = "TRI_BELOW_MIN"
    DELTA_SELF_LEGITIMATION = "DELTA_SELF_LEGITIMATION"
    SIGMA_ENTROPY_DRIFT = "SIGMA_ENTROPY_DRIFT"
    THETA_CIRCULAR_VALIDATION = "THETA_CIRCULAR_VALIDATION"
    OMEGA_SOCIAL_PROOF = "OMEGA_SOCIAL_PROOF"

@dataclass
class ProcessingConfig:
    version: str = "6.5"
    operational_mode: OperationalMode = OperationalMode.STABLE_LOCK
    processing_mode: ProcessingMode = ProcessingMode.HYBRID_PROCESSING
    tri_enabled: bool = True
    tri_strict_mode: bool = False
    tri_min_score: float = 0.90
    quarantine_enabled: bool = True
    neutralization_threshold: float = 0.75
    pattern_neutralization_enabled: bool = False  # enabled in Phase 2
    per_layer_budget_ms: Dict[str, float] = field(default_factory=lambda: {
        'delta': 5.0, 'sigma': 5.0, 'theta': 5.0, 'omega': 5.0
    })
    max_processing_time_ms: float = 50.0
    thresholds: Dict[str, float] = field(default_factory=lambda: {
        'delta': 0.85, 'sigma': 0.95, 'theta': 0.88, 'omega': 0.90
    })
