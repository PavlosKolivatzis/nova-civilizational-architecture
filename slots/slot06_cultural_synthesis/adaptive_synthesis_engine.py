from __future__ import annotations
from warnings import warn
from .engine import CulturalSynthesisEngine as _CSE
from .adapter import CulturalSynthesisAdapter as _CSA

warn(
    "Slot6: 'adaptive_synthesis_engine' is deprecated; "
    "use 'engine.CulturalSynthesisEngine' and 'adapter.CulturalSynthesisAdapter' instead.",
    DeprecationWarning,
    stacklevel=2,
)


class AdaptiveSynthesisEngine(_CSE):
    """Deprecated alias for CulturalSynthesisEngine."""
    pass


class AdaptiveSynthesisAdapter(_CSA):
    """Deprecated alias for CulturalSynthesisAdapter."""
    pass


# also export the multicultural names here for belt-and-suspenders compatibility
class MulticulturalTruthSynthesis(_CSE):
    pass


class MulticulturalTruthSynthesisAdapter(_CSA):
    pass


__all__ = [
    "AdaptiveSynthesisEngine",
    "AdaptiveSynthesisAdapter",
    "MulticulturalTruthSynthesis",
    "MulticulturalTruthSynthesisAdapter",
]
