"""Semantic Mirror utility functions and compatibility shims."""

from typing import Any, Optional


def mirror_get(mirror, key: str, default: Optional[Any] = None, requester: str = "unknown_slot") -> Optional[Any]:
    """
    Compatibility shim for both Semantic Mirror APIs:
      - new: mirror.get_context(key, default=...)
      - old: mirror.get_context(key, requester)

    Args:
        mirror: SemanticMirror instance
        key: Context key to retrieve
        default: Default value if key not found
        requester: Slot identifier for access control

    Returns:
        Context value or default
    """
    try:
        # Try newer API signature first
        return mirror.get_context(key, default=default)
    except TypeError:
        try:
            # Fallback to older positional signature
            result = mirror.get_context(key, requester)
            return result if result is not None else default
        except (TypeError, AttributeError):
            return default


def get_safe_mirror():
    """
    Safely import and get semantic mirror instance.

    Returns:
        SemanticMirror instance or None if unavailable
    """
    try:
        from nova.orchestrator.semantic_mirror import get_semantic_mirror
        return get_semantic_mirror()
    except Exception:
        return None


def emit_mirror_metric(slot: str, key: str, metric_type: str = "read"):
    """
    Emit mirror usage metrics for observability.

    Args:
        slot: Slot identifier (e.g. "slot03_emotional_matrix")
        key: Mirror key accessed
        metric_type: Type of operation ("read", "fallback_env", "tri_none")
    """
    # TODO: Wire to actual metrics system when available
    # For now, log for observability
    import logging
    logger = logging.getLogger("mirror_metrics")
    logger.debug(f"mirror_{metric_type}_total slot={slot} key={key}")
