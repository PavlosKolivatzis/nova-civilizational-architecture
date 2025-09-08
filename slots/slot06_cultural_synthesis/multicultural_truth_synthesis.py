from warnings import warn

from .engine import CulturalSynthesisEngine

warn(
    "Slot6: 'multicultural_truth_synthesis' is deprecated; use 'engine.CulturalSynthesisEngine' instead.",
    DeprecationWarning,
    stacklevel=2,
)


class MulticulturalTruthSynthesis(CulturalSynthesisEngine):
    """Deprecated alias for CulturalSynthesisEngine."""
    pass


__all__ = ["MulticulturalTruthSynthesis"]
