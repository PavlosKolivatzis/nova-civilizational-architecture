"""
Health check for Slot 1 - Truth Anchor.
"""
from . import truth_anchor_engine

# Cache engine instance to avoid re-initialization on every health check
_engine_instance = None


def health() -> dict:
    """Return health status of Truth Anchor slot."""
    global _engine_instance

    try:
        # Basic self-check - verify engine can be initialized (with caching)
        if _engine_instance is None:
            _engine_instance = truth_anchor_engine.TruthAnchorEngine()
        engine = _engine_instance

        return {
            "self_check": "ok",
            "engine_status": "operational",
            "version": getattr(truth_anchor_engine, "__version__", "0.1.0"),
            "capabilities": [
                "truth_verification",
                "reality_anchoring",
                "temporal_consistency",
            ],
            "metrics": {
                "cache_size": getattr(engine, "cache_size", 0),
                "active_connections": getattr(engine, "active_connections", 0),
            },
        }
    except Exception as e:  # pragma: no cover - defensive
        return {
            "self_check": "error",
            "error": str(e),
            "engine_status": "degraded",
        }
