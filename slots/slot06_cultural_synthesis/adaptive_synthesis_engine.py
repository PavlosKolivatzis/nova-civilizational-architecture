"""Deprecated legacy shim for the adaptive synthesis engine API."""

from __future__ import annotations

from warnings import warn

from .engine import CulturalSynthesisEngine as _CSE
from .adapter import CulturalSynthesisAdapter as _CSA

warn(
    "Slot6: 'adaptive_synthesis_engine' is deprecated; use "
    "'engine.CulturalSynthesisEngine' and 'adapter.CulturalSynthesisAdapter' instead.",
    DeprecationWarning,
    stacklevel=2,
)


class AdaptiveSynthesisEngine(_CSE):
    """Deprecated alias for :class:`CulturalSynthesisEngine`."""


class AdaptiveSynthesisAdapter(_CSA):
    """Deprecated adapter alias for compatibility."""


# For belt-and-suspenders compatibility, also expose the multicultural names here.
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
