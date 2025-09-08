import warnings
from .engine import CulturalSynthesisEngine

warnings.warn(
    "MulticulturalTruthSynthesis is deprecated; use CulturalSynthesisEngine instead.",
    DeprecationWarning,
    stacklevel=2,
)


class MulticulturalTruthSynthesis(CulturalSynthesisEngine):
    """Deprecated alias for :class:`CulturalSynthesisEngine`."""
    pass
