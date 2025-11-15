"""
Enhanced Health Check for Slot 7 - Production Controls

Provides comprehensive health status including circuit breaker state,
processing metrics, safeguard status, and reflex emission capabilities.
"""
import time
import hashlib
from typing import Dict, Any
from . import production_control_engine
from .metrics import get_slot7_metrics


def health() -> Dict[str, Any]:
    """
    Return comprehensive health status for Slot 7 Production Controls.

    Integrates rich engine health data, metrics summary, and reflex capabilities.
    Includes circuit breaker state, processing pressure, and policy configuration.
    """
    try:
        # Initialize engine and metrics
        engine = production_control_engine.ProductionControlEngine()
        metrics_collector = get_slot7_metrics(engine)

        # Get comprehensive engine health check
        engine_health = engine.health_check()

        # Get metrics summary for health context
        metrics_summary = metrics_collector.get_health_metrics_summary()

        # Calculate policy hash for configuration drift detection
        policy_hash = _calculate_policy_hash(engine.config)

        # Determine overall health status
        overall_status = _determine_overall_health_status(engine_health, metrics_summary)

        # Get circuit breaker pressure level
        pressure_level = _calculate_pressure_level(engine, metrics_summary)

        # Build comprehensive health payload
        health_payload = {
            # Core health information
            "self_check": "ok",
            "engine_status": "operational" if engine_health.get("status") == "healthy" else "degraded",
            "status_alias": engine_health.get("status", "healthy"),
            "overall_status": overall_status,
            "version": getattr(production_control_engine.ProductionControlEngine, "__version__", "2.0.0"),
            "timestamp": time.time(),

            # Circuit breaker state details
            "circuit_breaker": {
                "state": metrics_summary.get("circuit_breaker_state", "closed"),
                "failure_count": engine.circuit_breaker.failure_count,
                "success_count": engine.circuit_breaker.success_count,
                "last_failure_time": engine.circuit_breaker.last_failure_time,
                "last_success_time": engine.circuit_breaker.last_success_time,
                "failure_threshold": engine.circuit_breaker.failure_threshold,
                "pressure_level": pressure_level
            },

            # Processing performance metrics
            "processing": {
                "total_requests": metrics_summary.get("total_requests", 0),
                "success_rate": metrics_summary.get("success_rate", 1.0),
                "avg_response_time_ms": metrics_summary.get("avg_response_time_ms", 0.0),
                "active_requests": engine.resource_protector.active_requests,
                "max_concurrent": engine.resource_protector.max_concurrent_requests
            },

            # Safeguard status
            "safeguards": {
                "active": engine._get_active_safeguards(),
                "rate_limiter_tokens": engine.rate_limiter.tokens,
                "circuit_breaker_trips": metrics_summary.get("reflex_emissions_total", 0),
                "rate_limit_violations": engine.metrics.rate_limit_violations,
                "resource_violations": engine.metrics.resource_limit_violations
            },

            # Reflex emission capabilities
            "reflex_capabilities": {
                "emission_enabled": _is_reflex_enabled(),
                "shadow_mode": _is_reflex_shadow_mode(),
                "api_version": "1",
                "total_emissions": metrics_summary.get("reflex_emissions_total", 0),
                "recent_rate_per_minute": metrics_summary.get("reflex_rate_per_minute", 0.0),
                "supported_signals": ["breaker_pressure", "memory_pressure", "integrity_violation"]
            },

            # Configuration and policy
            "policy": {
                "policy_hash": policy_hash,
                "hot_reload_enabled": getattr(engine, 'hot_reload_enabled', False),
                "monitoring_enabled": engine._monitoring_enabled,
                "graceful_degradation": engine.failover_config.get("graceful_degradation_enabled", False)
            },

            # Operational metadata
            "capabilities": [
                "circuit_breaker",
                "rate_limiting",
                "resource_protection",
                "graceful_degradation",
                "reflex_emission",
                "metrics_export",
                "health_monitoring"
            ],

            # Issues and recommendations
            "health_issues": engine_health.get("issues", []) + metrics_summary.get("metrics_issues", []),
            "last_trip_timestamp": engine.circuit_breaker.last_failure_time,
            "next_reset_eligible": _calculate_next_reset_time(engine.circuit_breaker)
        }

        # Add schema provenance for contract compliance
        health_payload.update(_get_health_provenance())

        return health_payload

    except Exception as exc:  # pragma: no cover - defensive
        return {
            "self_check": "error",
            "error": str(exc),
            "engine_status": "critical_failure",
            "overall_status": "critical_failure",
            "timestamp": time.time(),
            **_get_health_provenance()
        }


def _calculate_policy_hash(config: Dict[str, Any]) -> str:
    """Calculate hash of current policy configuration for drift detection."""
    # Create stable hash of configuration
    config_str = str(sorted(config.items()))
    return hashlib.sha256(config_str.encode()).hexdigest()[:16]


def _determine_overall_health_status(engine_health: Dict[str, Any], metrics_summary: Dict[str, Any]) -> str:
    """Determine overall health status from engine and metrics data."""
    engine_status = engine_health.get("status", "healthy")
    metrics_status = metrics_summary.get("metrics_status", "healthy")

    # Prioritize worst status
    if engine_status == "degraded" or metrics_status == "degraded":
        return "degraded"
    elif engine_status == "critical_failure":
        return "critical_failure"
    else:
        return "healthy"


def _calculate_pressure_level(engine: production_control_engine.ProductionControlEngine,
                            metrics_summary: Dict[str, Any]) -> float:
    """Calculate current system pressure level (0.0-1.0)."""
    # Base pressure from circuit breaker state
    circuit_state = metrics_summary.get("circuit_breaker_state", "closed")
    if circuit_state == "open":
        return 1.0
    elif circuit_state == "half-open":
        return 0.7

    # Calculate pressure from failure rate and response times
    success_rate = metrics_summary.get("success_rate", 1.0)
    failure_pressure = max(0.0, (0.9 - success_rate) / 0.9)  # Pressure increases as success drops below 90%

    # Factor in response time pressure
    avg_response_time = metrics_summary.get("avg_response_time_ms", 0.0)
    response_pressure = min(1.0, avg_response_time / 1000.0)  # 1s+ response time = high pressure

    # Combine pressure factors
    total_pressure = min(1.0, max(failure_pressure, response_pressure * 0.5))

    return round(total_pressure, 3)


def _calculate_next_reset_time(circuit_breaker) -> float:
    """Calculate when circuit breaker will next be eligible for reset."""
    if circuit_breaker.state != "open" or not circuit_breaker._opened_at:
        return 0.0

    return circuit_breaker._opened_at + circuit_breaker.reset_timeout


def _is_reflex_enabled() -> bool:
    """Check if reflex emission is enabled via feature flags."""
    import os
    return os.getenv("NOVA_REFLEX_ENABLED", "0").strip() == "1"


def _is_reflex_shadow_mode() -> bool:
    """Check if reflex emission is in shadow mode."""
    import os
    return os.getenv("NOVA_REFLEX_SHADOW", "1").strip() == "1"


def _get_health_provenance() -> Dict[str, Any]:
    """Get health schema provenance for contract compliance."""
    try:
        from orchestrator.contracts.provenance import slot7_provenance
        return slot7_provenance()
    except ImportError:
        # Fallback provenance if centralized module not available
        return {
            "schema_id": "https://github.com/PavlosKolivatzis/nova-civilizational-architecture/schemas/slot7_production_controls_health_schema.json",
            "schema_version": "1"
        }
