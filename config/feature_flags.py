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
