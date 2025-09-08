from __future__ import annotations
from warnings import warn
from .engine import CulturalSynthesisEngine as _CSE
from .adapter import CulturalSynthesisAdapter as _CSA

warn(
    "Slot6: 'multicultural_truth_synthesis' is deprecated; "
    "use 'engine.CulturalSynthesisEngine' and 'adapter.CulturalSynthesisAdapter' instead.",
    DeprecationWarning,
    stacklevel=2,
)


class MulticulturalTruthSynthesis(_CSE):
    """Deprecated alias for CulturalSynthesisEngine."""
    pass


class AdaptiveSynthesisEngine(_CSE):
    """Deprecated alias for CulturalSynthesisEngine."""
    pass


class MulticulturalTruthSynthesisAdapter(_CSA):  # deprecated adapter alias
    """Deprecated alias for CulturalSynthesisAdapter."""
    pass


__all__ = [
    "MulticulturalTruthSynthesis",
    "AdaptiveSynthesisEngine",
    "MulticulturalTruthSynthesisAdapter",
]
