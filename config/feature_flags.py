"""Centralized feature flag and configuration management."""
import os
from typing import Any, Dict


def get_feature_flag(name: str, default: Any = None) -> Any:
    """Get feature flag value with proper type conversion"""
    value = os.getenv(name)
    if value is None:
        return default
    if isinstance(default, bool):
        return value.lower() in ("true", "1", "yes", "on")
    if isinstance(default, int):
        return int(value)
    if isinstance(default, float):
        return float(value)
    if isinstance(default, list):
        return value.split(',')
    return value


IDS_ENABLED = get_feature_flag("IDS_ENABLED", True)
IDS_WEIGHT = get_feature_flag("IDS_WEIGHT", 0.1)
IDS_SANDBOX_ONLY = get_feature_flag("IDS_SANDBOX_ONLY", True)
IDS_SCHEMA_VALIDATE = get_feature_flag("IDS_SCHEMA_VALIDATE", False)
IDS_ALLOWED_SCOPES = get_feature_flag(
    "IDS_ALLOWED_SCOPES", ["traits", "content", "signals", "memory"]
)
IDS_STRICT_SCOPE_VALIDATE = get_feature_flag("IDS_STRICT_SCOPE_VALIDATE", False)

IDS_ALPHA = get_feature_flag("IDS_ALPHA", 0.9)
IDS_BETA = get_feature_flag("IDS_BETA", 0.8)
IDS_EMA_LAMBDA = get_feature_flag("IDS_EMA_LAMBDA", 0.7)

IDS_STABLE_THRESHOLD = get_feature_flag("IDS_STABLE_THRESHOLD", 0.75)
IDS_REINTEGRATING_THRESHOLD = get_feature_flag("IDS_REINTEGRATING_THRESHOLD", 0.5)
IDS_DIVERGING_THRESHOLD = get_feature_flag("IDS_DIVERGING_THRESHOLD", 0.25)


# Slot 7 Production Controls Configuration
PRODUCTION_CONTROLS_ENABLED = get_feature_flag("PRODUCTION_CONTROLS_ENABLED", True)
CIRCUIT_BREAKER_ENABLED = get_feature_flag("CIRCUIT_BREAKER_ENABLED", True)
CIRCUIT_BREAKER_FAILURE_THRESHOLD = get_feature_flag("CIRCUIT_BREAKER_FAILURE_THRESHOLD", 5)
CIRCUIT_BREAKER_ERROR_THRESHOLD = get_feature_flag("CIRCUIT_BREAKER_ERROR_THRESHOLD", 0.5)
CIRCUIT_BREAKER_RESET_TIMEOUT = get_feature_flag("CIRCUIT_BREAKER_RESET_TIMEOUT", 60.0)
CIRCUIT_BREAKER_RECOVERY_TIME = get_feature_flag("CIRCUIT_BREAKER_RECOVERY_TIME", 60)

# Safety and Rate Limiting Configuration
RATE_LIMIT_ENABLED = get_feature_flag("RATE_LIMIT_ENABLED", True)
RATE_LIMIT_REQUESTS_PER_MINUTE = get_feature_flag("RATE_LIMIT_REQUESTS_PER_MINUTE", 100)
RATE_LIMIT_BURST_SIZE = get_feature_flag("RATE_LIMIT_BURST_SIZE", 10)

# Resource Protection Configuration
RESOURCE_PROTECTION_ENABLED = get_feature_flag("RESOURCE_PROTECTION_ENABLED", True)
MAX_PAYLOAD_SIZE_MB = get_feature_flag("MAX_PAYLOAD_SIZE_MB", 10)
MAX_PROCESSING_TIME_SECONDS = get_feature_flag("MAX_PROCESSING_TIME_SECONDS", 30)
MAX_CONCURRENT_REQUESTS = get_feature_flag("MAX_CONCURRENT_REQUESTS", 50)

# Health Check and Monitoring Configuration
HEALTH_CHECK_ENABLED = get_feature_flag("HEALTH_CHECK_ENABLED", True)
HEALTH_CHECK_INTERVAL_SECONDS = get_feature_flag("HEALTH_CHECK_INTERVAL_SECONDS", 10)
METRICS_COLLECTION_ENABLED = get_feature_flag("METRICS_COLLECTION_ENABLED", True)
ALERT_ON_CIRCUIT_BREAKER_TRIP = get_feature_flag("ALERT_ON_CIRCUIT_BREAKER_TRIP", True)

# Failover and Backup Configuration
FAILOVER_ENABLED = get_feature_flag("FAILOVER_ENABLED", True)
BACKUP_MODE_ENABLED = get_feature_flag("BACKUP_MODE_ENABLED", False)
GRACEFUL_DEGRADATION_ENABLED = get_feature_flag("GRACEFUL_DEGRADATION_ENABLED", True)


def get_ids_config() -> Dict[str, Any]:
    """Get complete IDS configuration"""
    return {
        "enabled": IDS_ENABLED,
        "weight": IDS_WEIGHT,
        "sandbox_only": IDS_SANDBOX_ONLY,
        "alpha": IDS_ALPHA,
        "beta": IDS_BETA,
        "ema_lambda": IDS_EMA_LAMBDA,
        "stable_threshold": IDS_STABLE_THRESHOLD,
        "reintegrating_threshold": IDS_REINTEGRATING_THRESHOLD,
        "diverging_threshold": IDS_DIVERGING_THRESHOLD,
        "allowed_scopes": IDS_ALLOWED_SCOPES,
        "strict_scope_validate": IDS_STRICT_SCOPE_VALIDATE,
    }


def get_production_controls_config() -> Dict[str, Any]:
    """Get complete production controls configuration"""
    return {
        "enabled": PRODUCTION_CONTROLS_ENABLED,
        "circuit_breaker": {
            "enabled": CIRCUIT_BREAKER_ENABLED,
            "failure_threshold": CIRCUIT_BREAKER_FAILURE_THRESHOLD,
            "error_threshold": CIRCUIT_BREAKER_ERROR_THRESHOLD,
            "reset_timeout": CIRCUIT_BREAKER_RESET_TIMEOUT,
            "recovery_time": CIRCUIT_BREAKER_RECOVERY_TIME,
        },
        "rate_limiting": {
            "enabled": RATE_LIMIT_ENABLED,
            "requests_per_minute": RATE_LIMIT_REQUESTS_PER_MINUTE,
            "burst_size": RATE_LIMIT_BURST_SIZE,
        },
        "resource_protection": {
            "enabled": RESOURCE_PROTECTION_ENABLED,
            "max_payload_size_mb": MAX_PAYLOAD_SIZE_MB,
            "max_processing_time_seconds": MAX_PROCESSING_TIME_SECONDS,
            "max_concurrent_requests": MAX_CONCURRENT_REQUESTS,
        },
        "monitoring": {
            "health_check_enabled": HEALTH_CHECK_ENABLED,
            "health_check_interval": HEALTH_CHECK_INTERVAL_SECONDS,
            "metrics_collection_enabled": METRICS_COLLECTION_ENABLED,
            "alert_on_circuit_breaker_trip": ALERT_ON_CIRCUIT_BREAKER_TRIP,
        },
        "failover": {
            "enabled": FAILOVER_ENABLED,
            "backup_mode_enabled": BACKUP_MODE_ENABLED,
            "graceful_degradation_enabled": GRACEFUL_DEGRADATION_ENABLED,
        }
    }
