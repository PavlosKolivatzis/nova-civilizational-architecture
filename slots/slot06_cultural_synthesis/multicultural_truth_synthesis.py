from warnings import warn

from .engine import CulturalSynthesisEngine
from .adapter import CulturalSynthesisAdapter

warn(
    "Slot6: 'multicultural_truth_synthesis' is deprecated; use 'engine.CulturalSynthesisEngine' and 'adapter.CulturalSynthesisAdapter' instead.",
    DeprecationWarning,
    stacklevel=2,
)


class AdaptiveSynthesisEngine(CulturalSynthesisEngine):
    """Deprecated alias for CulturalSynthesisEngine."""
    pass


class MulticulturalTruthSynthesisAdapter(CulturalSynthesisAdapter):
    """Deprecated alias for CulturalSynthesisAdapter."""
    pass


class MulticulturalTruthSynthesis(CulturalSynthesisEngine):
    """Deprecated alias for CulturalSynthesisEngine."""
    pass


__all__ = ["AdaptiveSynthesisEngine", "MulticulturalTruthSynthesisAdapter", "MulticulturalTruthSynthesis"]
