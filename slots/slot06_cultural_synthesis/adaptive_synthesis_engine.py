from __future__ import annotations

from warnings import warn

from .multicultural_truth_synthesis import (
    MulticulturalTruthSynthesis as _BaseCompat,
    MulticulturalTruthSynthesisAdapter as _CSA,
)

warn(
    "Slot6: 'adaptive_synthesis_engine' is deprecated; "
    "use 'engine.CulturalSynthesisEngine' and 'adapter.CulturalSynthesisAdapter' instead.",
    DeprecationWarning,
    stacklevel=2,
)


class AdaptiveSynthesisEngine(_BaseCompat):
    pass


class AdaptiveSynthesisAdapter(_CSA):
    pass


__all__ = ["AdaptiveSynthesisEngine", "AdaptiveSynthesisAdapter"]

