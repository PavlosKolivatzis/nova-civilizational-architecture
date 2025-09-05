"""Enhanced configuration system for ΔTHRESH Slot 2.

This module extends the basic :class:`ProcessingConfig` used in the
"slot02_deltathresh" package with additional capabilities required for
production deployments.  Key features include:

* environment aware settings with ``from_environment`` helpers
* pluggable logging/monitoring/security sub-configs
* ability to serialise to and from dictionaries for persistence
* basic runtime validation used by ``ConfigManager``

The goal is to provide a configuration object that remains backwards
compatible with existing tests and processor logic while adding
foundational pieces for future expansion (hot reload, metrics export,
secret management, etc.).
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
from pathlib import Path
from typing import Dict, Optional, Tuple

import json
import os
import yaml

from dotenv import load_dotenv

from ..config import ProcessingConfig, OperationalMode, ProcessingMode


# ---------------------------------------------------------------------------
# helper enums and nested configs
# ---------------------------------------------------------------------------


class Environment(str, Enum):
    """Deployment environment the slot is running in."""

    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"
    TEST = "test"


class LogLevel(str, Enum):
    """Simple log level enum used by :class:`LoggingConfig`."""

    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


@dataclass
class LoggingConfig:
    level: LogLevel = LogLevel.INFO
    format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    file_path: Optional[Path] = None


@dataclass
class MonitoringConfig:
    enabled: bool = True
    prometheus_endpoint: str = "0.0.0.0:9090"
    metrics_export_interval: int = 30


@dataclass
class SecurityConfig:
    enable_authentication: bool = True
    jwt_secret: Optional[str] = None


@dataclass
class CacheConfig:
    enabled: bool = True
    max_size: int = 10000
    ttl_seconds: int = 300


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

    # New enhanced sections
    environment: Environment = Environment.PRODUCTION
    logging: LoggingConfig = field(default_factory=LoggingConfig)
    monitoring: MonitoringConfig = field(default_factory=MonitoringConfig)
    security: SecurityConfig = field(default_factory=SecurityConfig)
    cache: CacheConfig = field(default_factory=CacheConfig)

    # ------------------------------------------------------------------
    # construction helpers
    # ------------------------------------------------------------------

    @classmethod
    def from_environment(cls) -> "EnhancedProcessingConfig":
        """Create configuration using environment variables as overrides."""

        load_dotenv()
        cfg = cls()

        env = os.getenv("SLOT2_ENV")
        if env:
            cfg.environment = Environment(env.lower())

        op_mode = os.getenv("OPERATIONAL_MODE")
        if op_mode:
            cfg.operational_mode = OperationalMode(op_mode.lower())

        proc_mode = os.getenv("PROCESSING_MODE")
        if proc_mode:
            cfg.processing_mode = ProcessingMode(proc_mode.lower())

        log_level = os.getenv("LOG_LEVEL")
        if log_level:
            cfg.logging.level = LogLevel(log_level.upper())

        jwt = os.getenv("JWT_SECRET")
        if jwt:
            cfg.security.jwt_secret = jwt

        return cfg

    @classmethod
    def from_dict(cls, data: Dict) -> "EnhancedProcessingConfig":
        """Create a config from a nested dictionary."""

        cfg = cls()
        for key, value in data.items():
            if not hasattr(cfg, key):
                continue
            current = getattr(cfg, key)
            if isinstance(current, (LoggingConfig, MonitoringConfig, SecurityConfig, CacheConfig)) and isinstance(value, dict):
                nested_cls = type(current)
                if nested_cls is LoggingConfig and "level" in value:
                    value = {**value, "level": LogLevel(value["level"])}
                setattr(cfg, key, nested_cls(**value))
            else:
                # handle enum conversion for top-level fields
                if key == "operational_mode":
                    setattr(cfg, key, OperationalMode(value))
                elif key == "processing_mode":
                    setattr(cfg, key, ProcessingMode(value))
                elif key == "environment":
                    setattr(cfg, key, Environment(value))
                else:
                    setattr(cfg, key, value)
        return cfg

    def to_dict(self) -> Dict:
        """Serialise configuration to a dictionary."""

        return asdict(self)

    # ------------------------------------------------------------------
    # validation
    # ------------------------------------------------------------------

    def validate_runtime(self) -> Tuple[bool, list]:
        """Perform lightweight runtime validation."""

        violations = []
        if self.environment is Environment.PRODUCTION and self.security.enable_authentication:
            if not self.security.jwt_secret:
                violations.append("JWT secret must be set in production")
        return (len(violations) == 0, violations)
