"""Tests for deprecated Slot 6 compatibility shims."""

import sys
from pathlib import Path


def test_legacy_imports_exist():
    sys.path.append(str(Path(__file__).resolve().parents[2] / "slots"))
    from slot06_cultural_synthesis.multicultural_truth_synthesis import (
        AdaptiveSynthesisEngine,
        MulticulturalTruthSynthesisAdapter,
    )
    from slot06_cultural_synthesis.engine import CulturalSynthesisEngine
    from slot06_cultural_synthesis.adapter import CulturalSynthesisAdapter

    assert issubclass(AdaptiveSynthesisEngine, CulturalSynthesisEngine)
    assert issubclass(
        MulticulturalTruthSynthesisAdapter, CulturalSynthesisAdapter
    )

