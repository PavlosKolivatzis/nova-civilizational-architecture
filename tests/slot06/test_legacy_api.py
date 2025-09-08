"""Regression test for legacy analyze_and_simulate compatibility."""

import sys
from pathlib import Path


def test_legacy_analyze_and_simulate_returns_attributes():
    sys.path.append(str(Path(__file__).resolve().parents[2] / "slots"))
    from slot06_cultural_synthesis.multicultural_truth_synthesis import (
        AdaptiveSynthesisEngine,
    )

    eng = AdaptiveSynthesisEngine()
    res = eng.analyze_and_simulate(
        "inst",
        "hello world",
        profile={"consent_ok": True},
        slot2_result={"tri_score": 0.6, "layer_scores": {}, "forbidden_hits": []},
    )

    assert hasattr(res, "adaptation_effectiveness")
    assert hasattr(res, "principle_preservation_score")

