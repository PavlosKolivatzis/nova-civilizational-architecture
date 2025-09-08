import warnings
from .engine import CulturalSynthesisEngine

warnings.warn(
    "AdaptiveSynthesisEngine is deprecated; use CulturalSynthesisEngine instead.",
    DeprecationWarning,
    stacklevel=2,
)


class AdaptiveSynthesisEngine(CulturalSynthesisEngine):
    """Deprecated alias for :class:`CulturalSynthesisEngine`."""
    pass
