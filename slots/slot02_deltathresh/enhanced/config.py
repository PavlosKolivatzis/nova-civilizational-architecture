from dataclasses import dataclass
from ..config import ProcessingConfig, OperationalMode, ProcessingMode


@dataclass
class EnhancedProcessingConfig(ProcessingConfig):
    """Extended configuration with performance and feature flags."""

    # TRI scoring controls
    tri_enabled: bool = True
    tri_min_score: float = 0.85
    tri_strict_mode: bool = False

    # Layer thresholds
    delta_threshold: float = 0.7
    sigma_threshold: float = 0.6
    theta_threshold: float = 0.65
    omega_threshold: float = 0.55

    # Processing feature toggles
    quarantine_enabled: bool = True
    pattern_neutralization_enabled: bool = True
    neutralization_threshold: float = 0.8

    # Caching and batching
    cache_enabled: bool = True
    cache_ttl_seconds: int = 300
    batch_processing: bool = False
    batch_size: int = 10

    # Performance knobs
    performance_budget_ms: float = 35.0
    adaptive_thresholds: bool = True
    realtime_metrics: bool = True

    # Content limits
    max_content_length: int = 10000
