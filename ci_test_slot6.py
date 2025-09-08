from pathlib import Path
import sys

# Ensure local slots directory is on the import path
sys.path.append(str(Path(__file__).resolve().parent / "slots"))

from slot06_cultural_synthesis.engine import CulturalSynthesisEngine
from slot06_cultural_synthesis.adapter import CulturalSynthesisAdapter


if __name__ == "__main__":
    engine = CulturalSynthesisAdapter(CulturalSynthesisEngine())
    profile = engine.analyze_cultural_context('TestInstitution', {'region': 'EU'})
    assert profile['adaptation_effectiveness'] >= 0
    print(f"\u2705 Slot 6 v7.4.1 test passed: effectiveness={profile['adaptation_effectiveness']:.3f}")
