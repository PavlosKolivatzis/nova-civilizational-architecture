from .engine import (
    CulturalSynthesisEngine,
    CulturalProfile,
    SynthesisConfig,
    GuardrailValidationResult,
)
from .adapter import MulticulturalTruthSynthesisAdapter

# Backwards compatibility alias
MulticulturalTruthSynthesis = MulticulturalTruthSynthesisAdapter

__all__ = [
    "CulturalSynthesisEngine",
    "MulticulturalTruthSynthesisAdapter",
    "MulticulturalTruthSynthesis",
    "CulturalProfile",
    "SynthesisConfig",
    "GuardrailValidationResult",
]
