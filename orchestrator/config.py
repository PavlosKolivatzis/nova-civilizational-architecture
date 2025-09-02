"""System configuration with environment variable overrides."""

from dataclasses import dataclass, field
import os


@dataclass
class SystemConfig:
    # Truth verification
    TRUTH_THRESHOLD: float = float(os.getenv("NOVA_TRUTH_THRESHOLD", 0.87))

    # Cultural weighting (kept simple here)
    CULTURAL_WEIGHTS: dict = field(
        default_factory=lambda: {
            "western": 0.35,
            "eastern": 0.30,
            "indigenous": 0.25,
            "global": 0.10,
        }
    )

    # Performance
    MAX_CONCURRENT_PROCESSES: int = int(os.getenv("NOVA_MAX_CONCURRENT_PROCESSES", 12))
    MEMORY_ETHICS_ENABLED: bool = os.getenv("NOVA_MEMORY_ETHICS_ENABLED", "true").lower() == "true"
    DISTORTION_DETECTION_SENSITIVITY: float = float(os.getenv("NOVA_DISTORTION_DETECTION_SENSITIVITY", 0.92))

    # Runtime thresholds
    ROUTER_LATENCY_MS: float = float(os.getenv("NOVA_ROUTER_LATENCY_MS", 1000.0))
    ROUTER_ERROR_THRESHOLD: float = float(os.getenv("NOVA_ROUTER_ERROR_THRESHOLD", 0.2))
    ROUTER_TIMEOUT_MULTIPLIER: float = float(os.getenv("NOVA_ROUTER_TIMEOUT_MULTIPLIER", 1.5))
    ROUTER_TIMEOUT_CAP_S: float = float(os.getenv("NOVA_ROUTER_TIMEOUT_CAP_S", 30.0))

    # Deployment
    DEPLOYMENT_MODES: tuple[str, ...] = ("testing", "staging", "production")
    CURRENT_MODE: str = os.getenv("NOVA_CURRENT_MODE", "testing")


config = SystemConfig()
