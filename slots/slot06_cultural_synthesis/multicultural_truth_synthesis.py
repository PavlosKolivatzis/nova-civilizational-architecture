"""Legacy v7.x compatibility shims.

This module re-exports the modern engine and adapter under their former
names so that older CI scripts importing
``slot06_cultural_synthesis.multicultural_truth_synthesis`` keep working.
"""

from __future__ import annotations

from warnings import warn

from .engine import CulturalSynthesisEngine as _CSE
from .adapter import CulturalSynthesisAdapter as _CSA

warn(
    "Slot6: 'multicultural_truth_synthesis' is deprecated; use "
    "'engine.CulturalSynthesisEngine' and 'adapter.CulturalSynthesisAdapter' "
    "instead.",
    DeprecationWarning,
    stacklevel=2,
)


class MulticulturalTruthSynthesis(_CSE):
    """Deprecated alias for :class:`CulturalSynthesisEngine`."""


class AdaptiveSynthesisEngine(_CSE):
    """Deprecated alias kept for backward compatibility."""


class MulticulturalTruthSynthesisAdapter(_CSA):
    """Deprecated adapter alias for compatibility."""


__all__ = [
    "MulticulturalTruthSynthesis",
    "AdaptiveSynthesisEngine",
    "MulticulturalTruthSynthesisAdapter",
]
