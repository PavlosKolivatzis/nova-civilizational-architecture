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

# Slot 3 - Emotional Matrix Configuration
SLOT3_ESCALATION_ENABLED = get_feature_flag("SLOT3_ESCALATION_ENABLED", True)
SLOT3_RATE_PER_MIN = get_feature_flag("SLOT3_RATE_PER_MIN", 600)
SLOT3_SWING_WINDOW = get_feature_flag("SLOT3_SWING_WINDOW", 30)
SLOT3_SWING_DELTA = get_feature_flag("SLOT3_SWING_DELTA", 1.2)
SLOT3_PREVIEW_MAXLEN = get_feature_flag("SLOT3_PREVIEW_MAXLEN", 160)

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

# Observability and Phase 4.1 Metabolism Configuration
NOVA_ENABLE_PROMETHEUS = get_feature_flag("NOVA_ENABLE_PROMETHEUS", True)
NOVA_UNLEARN_ANOMALY = get_feature_flag("NOVA_UNLEARN_ANOMALY", True)
NOVA_SLOT06_W_TRI = get_feature_flag("NOVA_SLOT06_W_TRI", 0.7)
NOVA_SLOT07_W_PRESS = get_feature_flag("NOVA_SLOT07_W_PRESS", 0.8)
NOVA_SLOT10_W_JITTER = get_feature_flag("NOVA_SLOT10_W_JITTER", 0.3)
NOVA_UNLEARN_MIN_HALF_LIFE = get_feature_flag("NOVA_UNLEARN_MIN_HALF_LIFE", 60)
NOVA_UNLEARN_MAX_HALF_LIFE = get_feature_flag("NOVA_UNLEARN_MAX_HALF_LIFE", 1800)

# ANR (Adaptive Neural Routing) Configuration
NOVA_ANR_ENABLED = get_feature_flag("NOVA_ANR_ENABLED", True)
NOVA_ANR_PILOT = get_feature_flag("NOVA_ANR_PILOT", 0.0)
NOVA_ANR_LEARN_SHADOW = get_feature_flag("NOVA_ANR_LEARN_SHADOW", True)
NOVA_ANR_STRICT_ON_ANOMALY = get_feature_flag("NOVA_ANR_STRICT_ON_ANOMALY", True)
NOVA_ANR_MAX_FAST_PROB = get_feature_flag("NOVA_ANR_MAX_FAST_PROB", 0.15)

# Phase 6.0 Belief Propagation Configuration
NOVA_ENABLE_PROBABILISTIC_CONTRACTS = get_feature_flag("NOVA_ENABLE_PROBABILISTIC_CONTRACTS", True)

# Slot 10 Civilizational Deployment Configuration
NOVA_SLOT10_ENABLED = get_feature_flag("NOVA_SLOT10_ENABLED", True)

# META_LENS Configuration (Optional, flag-gated)
NOVA_ENABLE_META_LENS = get_feature_flag("NOVA_ENABLE_META_LENS", False)
META_LENS_MAX_ITERS = get_feature_flag("META_LENS_MAX_ITERS", 3)
META_LENS_ALPHA = get_feature_flag("META_LENS_ALPHA", 0.5)
META_LENS_EPSILON = get_feature_flag("META_LENS_EPSILON", 0.02)

# Phase 13 Autonomous Verification Ledger (AVL) Configuration
LEDGER_ENABLED = get_feature_flag("LEDGER_ENABLED", True)
LEDGER_TRUST_WEIGHT_FIDELITY = get_feature_flag("LEDGER_TRUST_WEIGHT_FIDELITY", 0.5)
LEDGER_TRUST_WEIGHT_PQC_RATE = get_feature_flag("LEDGER_TRUST_WEIGHT_PQC_RATE", 0.2)
LEDGER_TRUST_WEIGHT_VERIFY_RATE = get_feature_flag("LEDGER_TRUST_WEIGHT_VERIFY_RATE", 0.2)
LEDGER_TRUST_WEIGHT_CONTINUITY = get_feature_flag("LEDGER_TRUST_WEIGHT_CONTINUITY", 0.1)


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


def get_ledger_config() -> Dict[str, Any]:
    """Get complete ledger configuration (Phase 13 AVL)"""
    return {
        "enabled": LEDGER_ENABLED,
        "trust_weights": {
            "fidelity_mean": LEDGER_TRUST_WEIGHT_FIDELITY,
            "pqc_rate": LEDGER_TRUST_WEIGHT_PQC_RATE,
            "verify_rate": LEDGER_TRUST_WEIGHT_VERIFY_RATE,
            "continuity": LEDGER_TRUST_WEIGHT_CONTINUITY,
        }
    }
