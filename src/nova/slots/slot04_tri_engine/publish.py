"""TRI signals publisher to Semantic Mirror."""

from typing import Optional


def publish_tri_to_mirror(coherence: Optional[float],
                          phase_coherence: Optional[float],
                          phase_jitter: Optional[float]) -> None:
    """Publish TRI metrics to the Semantic Mirror with safe fallbacks."""
    try:
        from nova.orchestrator.semantic_mirror import get_semantic_mirror
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
    def _set(key: str, value: float, ttl: int = 120):
        try:
            mirror.set_context(key, value, ttl=ttl)
        except TypeError:
            try:
                mirror.set_context(key, value)
            except Exception:
                pass

    try:
        if coherence is not None:
            _set("slot04.coherence", float(coherence))
        if phase_coherence is not None:
            _set("slot04.phase_coherence", float(phase_coherence))
        if phase_jitter is not None:
            _set("slot04.phase_jitter", float(phase_jitter))
    except Exception:
        # Never let publishing break Slot4; mirror is advisory
        pass
