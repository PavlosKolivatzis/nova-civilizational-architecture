"""
System configuration with environment variable overrides.
"""
from pydantic import Field
from pydantic_settings import BaseSettings


class SystemConfig(BaseSettings):
    # Truth verification
    TRUTH_THRESHOLD: float = Field(0.87, ge=0.0, le=1.0)

    # Cultural weighting (kept simple here; load from JSON/YAML if needed)
    CULTURAL_WEIGHTS: dict = {
        "western": 0.35,
        "eastern": 0.30,
        "indigenous": 0.25,
        "global": 0.10,
    }

    # Performance
    MAX_CONCURRENT_PROCESSES: int = 12
    MEMORY_ETHICS_ENABLED: bool = True
    DISTORTION_DETECTION_SENSITIVITY: float = 0.92

    # Runtime thresholds
    ROUTER_LATENCY_MS: float = 1000.0
    ROUTER_ERROR_THRESHOLD: float = 0.2
    ROUTER_TIMEOUT_MULTIPLIER: float = 1.5
    ROUTER_TIMEOUT_CAP_S: float = 30.0

    # Deployment
    DEPLOYMENT_MODES: tuple[str, ...] = ("testing", "staging", "production")
    CURRENT_MODE: str = "testing"

    class Config:
        env_prefix = "NOVA_"
        env_nested_delimiter = "__"  # e.g., NOVA_CULTURAL_WEIGHTS__western=0.4


config = SystemConfig()  # import and use
