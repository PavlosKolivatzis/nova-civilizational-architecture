"""Phase-lock publisher to Semantic Mirror."""

from typing import Optional


def publish_phase_lock_to_mirror(value: Optional[float]) -> None:
    """Publish phase-lock value to the Semantic Mirror with safe fallbacks."""
    if value is None:
        return

    try:
        from orchestrator.semantic_mirror import get_semantic_mirror
    except Exception:
        return  # mirror not available; safe no-op

    mirror = None
    try:
        mirror = get_semantic_mirror()
    except Exception:
        return

    if mirror is None:
        return

    # Support both set_context(key, value, ttl=...) and set_context(key, value)
    try:
        try:
            mirror.set_context("slot03.phase_lock", float(value), ttl=120)
        except TypeError:
            mirror.set_context("slot03.phase_lock", float(value))
    except Exception:
        # Never let publishing break Slot03; mirror is advisory
        pass