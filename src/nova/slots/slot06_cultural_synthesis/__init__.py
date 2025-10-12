from .engine import (
    CulturalSynthesisEngine,
    CulturalProfile,
    SynthesisConfig,
    GuardrailValidationResult,
)
from .adapter import CulturalSynthesisAdapter, MulticulturalTruthSynthesisAdapter

# Backwards compatibility alias
MulticulturalTruthSynthesis = MulticulturalTruthSynthesisAdapter

__all__ = [
    "CulturalSynthesisEngine",
    "CulturalSynthesisAdapter",
    "MulticulturalTruthSynthesisAdapter",
    "MulticulturalTruthSynthesis",
    "CulturalProfile",
    "SynthesisConfig",
    "GuardrailValidationResult",
]
