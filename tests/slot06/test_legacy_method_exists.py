"""Ensure monkey-patched legacy method returns attribute-style result."""

import sys
from pathlib import Path


def test_monkey_patched_engine_exposes_legacy_method():
    sys.path.append(str(Path(__file__).resolve().parents[2] / "slots"))

    # Importing the legacy module installs the compatibility method
    import slot06_cultural_synthesis.multicultural_truth_synthesis  # noqa: F401
    from slot06_cultural_synthesis.engine import CulturalSynthesisEngine

    eng = CulturalSynthesisEngine()
    res = eng.analyze_and_simulate(
        "inst",
        "hello",
        profile={"consent_ok": True},
        slot2_result={"tri_score": 0.6, "layer_scores": {}, "forbidden_hits": []},
    )

    assert hasattr(res, "adaptation_effectiveness")
    assert hasattr(res, "principle_preservation_score")

