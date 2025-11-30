"""
Semantic Mirror Setup and Integration

Provides setup functions for Flow Fabric Phase 3 deployment.
Handles initialization, configuration, and integration wiring.
"""
import logging
from typing import Dict, Any

from nova.orchestrator.semantic_mirror import get_semantic_mirror
from nova.orchestrator.config import config

logger = logging.getLogger(__name__)


def setup_semantic_mirror_integration() -> bool:
    """Setup Semantic Mirror integration across slots.

    Returns:
        True if setup successful, False otherwise
    """
    try:
        # Check feature flag
        semantic_mirror_enabled = getattr(config, 'SEMANTIC_MIRROR_ENABLED', False)
        if not semantic_mirror_enabled:
            logger.info("Semantic Mirror disabled by feature flag")
            return True  # Not enabled, but not an error

        # Initialize semantic mirror
        mirror = get_semantic_mirror()

        # Configure production access rules
        _configure_production_access_rules(mirror)

        # Setup Slot 7 context publishing
        _setup_slot7_context_publishing()

        # Setup Slot 6 context consumption
        _setup_slot6_context_consumption()

        logger.info("Semantic Mirror integration setup complete")
        return True

    except Exception as e:
        logger.error(f"Failed to setup Semantic Mirror integration: {e}")
        return False


def _configure_production_access_rules(mirror) -> None:
    """Configure production-ready access control rules."""
    production_rules = {
        # Slot 7 Production Controls -> Other Slots
        "slot07.breaker_state": [
            "slot06_cultural_synthesis",
            "slot03_emotional_matrix"
        ],
        "slot07.pressure_level": [
            "slot06_cultural_synthesis",
            "slot03_emotional_matrix",
            "slot01_truth_anchor"
        ],
        "slot07.resource_status": [
            "slot06_cultural_synthesis",
            "slot01_truth_anchor"
        ],
        "slot07.health_summary": [
            "slot06_cultural_synthesis",
            "slot03_emotional_matrix"
        ],
        "slot07.public_metrics": [
            "slot06_cultural_synthesis"
        ],

        # Slot 6 Cultural Synthesis -> Other Slots
        "slot06.cultural_profile": [
            "slot03_emotional_matrix",
            "slot07_production_controls"
        ],
        "slot06.adaptation_rate": [
            "slot03_emotional_matrix",
            "slot07_production_controls"
        ],
        "slot06.synthesis_complexity": [
            "slot07_production_controls"
        ],
        "slot06.synthesis_results": [
            "slot07_production_controls"
        ],

        # Slot 3 Emotional Matrix -> Limited Access
        "slot03.emotional_state": [
            "slot06_cultural_synthesis"
        ],
        "slot03.confidence_level": [
            "slot06_cultural_synthesis",
            "slot07_production_controls"
        ],

        # Cross-slot coordination contexts
        "system.coordination_state": [
            "slot01_truth_anchor",
            "slot03_emotional_matrix",
            "slot06_cultural_synthesis",
            "slot07_production_controls"
        ],

        # Router & governance contexts
        "router.constraint_snapshot": [
            "slot07_production_controls",
            "slot10_civilizational_deployment",
            "governance"
        ],
        "router.anr_policy": [
            "slot07_production_controls",
            "slot10_civilizational_deployment",
            "governance"
        ],
        "router.final_route": [
            "slot07_production_controls",
            "slot10_civilizational_deployment",
            "governance"
        ],

        # Temporal contexts
        "temporal.snapshot": [
            "router",
            "governance",
            "slot07_production_controls",
            "slot10_civilizational_deployment",
            "temporal_api"
        ],
        "temporal.ledger_head": [
            "governance",
            "slot10_civilizational_deployment",
            "temporal_api"
        ],
        "temporal.router_modifiers": [
            "governance",
            "slot07_production_controls",
            "slot10_civilizational_deployment"
        ],
        "predictive.prediction_snapshot": [
            "router",
            "governance",
            "slot07_production_controls",
            "slot10_civilizational_deployment"
        ],
        "predictive.ledger_head": [
            "governance",
            "router"
        ],
        "predictive.router_modifiers": [
            "governance",
            "slot07_production_controls",
            "slot10_civilizational_deployment"
        ],
    }

    mirror.configure_access_rules(production_rules)
    logger.info(f"Configured {len(production_rules)} production access rules")


def _setup_slot7_context_publishing() -> None:
    """Setup Slot 7 context publishing integration."""
    try:
        # Import here to avoid circular dependencies
        from nova.slots.slot07_production_controls.context_publisher import get_context_publisher
        from nova.slots.slot07_production_controls.production_control_engine import ProductionControlEngine

        # Get production engine instance
        # Note: In production, this would be the actual running engine instance
        engine = ProductionControlEngine()

        # Setup context publisher
        publisher = get_context_publisher(engine)

        # Configure publishing interval based on environment
        if config.CURRENT_MODE == "production":
            publisher.publish_interval_seconds = 30.0  # Less frequent in prod
        elif config.CURRENT_MODE == "staging":
            publisher.publish_interval_seconds = 15.0  # Moderate in staging
        else:
            publisher.publish_interval_seconds = 10.0  # Frequent in dev/testing

        logger.info(f"Configured Slot 7 context publishing (interval={publisher.publish_interval_seconds}s)")

    except ImportError as e:
        logger.warning(f"Slot 7 context publishing not available: {e}")
    except Exception as e:
        logger.error(f"Failed to setup Slot 7 context publishing: {e}")


def _setup_slot6_context_consumption() -> None:
    """Setup Slot 6 context-aware synthesis integration."""
    try:
        # Import here to avoid circular dependencies
        from nova.slots.slot06_cultural_synthesis.context_aware_synthesis import get_context_aware_synthesis

        # Initialize context-aware synthesis
        # Note: Base engine would be wired in production
        synthesis = get_context_aware_synthesis()

        # Configure context cache TTL based on environment
        if config.CURRENT_MODE == "production":
            synthesis.context_cache_ttl = 60.0  # Longer cache in prod
        else:
            synthesis.context_cache_ttl = 30.0  # Shorter cache in dev/staging

        logger.info(f"Configured Slot 6 context consumption (cache_ttl={synthesis.context_cache_ttl}s)")

    except ImportError as e:
        logger.warning(f"Slot 6 context consumption not available: {e}")
    except Exception as e:
        logger.error(f"Failed to setup Slot 6 context consumption: {e}")


def get_semantic_mirror_health() -> Dict[str, Any]:
    """Get Semantic Mirror health status for monitoring."""
    try:
        mirror = get_semantic_mirror()
        metrics = mirror.get_metrics()

        # Determine health status
        health_status = "healthy"
        issues = []

        # Check for potential issues
        if metrics["active_contexts"] == 0:
            issues.append("no_active_contexts")

        if metrics.get("queries_access_denied", 0) > metrics.get("queries_successful", 1) * 0.1:
            issues.append("high_access_denial_rate")

        if metrics.get("queries_rate_limited", 0) > 0:
            issues.append("rate_limiting_active")

        if issues:
            health_status = "degraded"

        return {
            "status": health_status,
            "issues": issues,
            "metrics": {
                "active_contexts": metrics["active_contexts"],
                "total_contexts": metrics["total_contexts"],
                "queries_successful": metrics.get("queries_successful", 0),
                "queries_access_denied": metrics.get("queries_access_denied", 0),
                "publications_total": metrics.get("publications_total", 0)
            },
            "feature_enabled": getattr(config, 'SEMANTIC_MIRROR_ENABLED', False),
            "timestamp": metrics.get("last_cleanup", 0)
        }

    except Exception as e:
        return {
            "status": "error",
            "issues": [f"health_check_failed: {str(e)}"],
            "metrics": {},
            "feature_enabled": False,
            "timestamp": 0
        }


def reset_semantic_mirror_integration() -> None:
    """Reset Semantic Mirror integration (for testing)."""
    from nova.orchestrator.semantic_mirror import reset_semantic_mirror
    from nova.slots.slot07_production_controls.context_publisher import reset_context_publisher
    from nova.slots.slot06_cultural_synthesis.context_aware_synthesis import reset_context_aware_synthesis

    reset_semantic_mirror()
    reset_context_publisher()
    reset_context_aware_synthesis()

    logger.info("Reset Semantic Mirror integration")
