from warnings import warn

from .engine import CulturalSynthesisEngine

warn(
    "Slot6: 'adaptive_synthesis_engine' is deprecated; use 'engine.CulturalSynthesisEngine' instead.",
    DeprecationWarning,
    stacklevel=2,
)


class AdaptiveSynthesisEngine(CulturalSynthesisEngine):
    """Deprecated alias for CulturalSynthesisEngine."""
    pass


__all__ = ["AdaptiveSynthesisEngine"]
