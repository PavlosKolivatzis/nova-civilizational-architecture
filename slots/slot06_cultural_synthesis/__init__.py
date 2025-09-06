from .engine import (
    AdaptiveSynthesisEngine,
    MulticulturalTruthSynthesisAdapter,
    CulturalProfile,
    GuardrailValidationResult,
)

# Backwards compatibility alias
MulticulturalTruthSynthesis = MulticulturalTruthSynthesisAdapter

__all__ = [
    "AdaptiveSynthesisEngine",
    "MulticulturalTruthSynthesisAdapter",
    "MulticulturalTruthSynthesis",
    "CulturalProfile",
    "GuardrailValidationResult",
]
