from slots.slot06_cultural_synthesis.multicultural_truth_synthesis import (
    AdaptiveSynthesisEngine,
    MulticulturalTruthSynthesisAdapter,
)
from slots.slot06_cultural_synthesis.engine import CulturalSynthesisEngine
from slots.slot06_cultural_synthesis.adapter import CulturalSynthesisAdapter


def test_legacy_imports_exist() -> None:
    assert issubclass(AdaptiveSynthesisEngine, CulturalSynthesisEngine)
    assert issubclass(
        MulticulturalTruthSynthesisAdapter, CulturalSynthesisAdapter
    )
