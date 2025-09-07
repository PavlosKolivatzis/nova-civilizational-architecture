from .engine import (
    AdaptiveSynthesisEngine,
    CulturalProfile,
    GuardrailValidationResult,
)
from .adapter import MulticulturalTruthSynthesisAdapter

# Backwards compatibility alias
MulticulturalTruthSynthesis = MulticulturalTruthSynthesisAdapter

__all__ = [
    "AdaptiveSynthesisEngine",
    "MulticulturalTruthSynthesisAdapter",
    "MulticulturalTruthSynthesis",
    "CulturalProfile",
    "GuardrailValidationResult",
]
