import math

from slots.slot06_cultural_synthesis.engine import CulturalSynthesisEngine, CulturalProfile


def test_synthesize_metrics() -> None:
    engine = CulturalSynthesisEngine()
    profile: CulturalProfile = {
        "clarity": 1.2,  # will be clamped to 1.0
        "foresight": -0.5,  # will be clamped to 0.0
        "empiricism": 0.8,
        "anchor_confidence": 0.6,
        "tri_score": 0.7,
        "layer_scores": {"a": 0.4, "b": 0.8},
        "ideology_push": True,
    }
    res = engine.synthesize(profile)

    expected_adaptation = (
        0.35 * 0.9 * 0.8
        + 0.25 * 0.8 * 1.0
        + 0.25 * 0.8 * 0.0
        + 0.10 * 0.7 * 1.0
        + 0.05 * 0.7 * (1 - abs(0.5 - 0.0) * 2)
    )
    expected_adaptation = max(0.0, min(1.0, expected_adaptation))
    expected_principle = 1.0 - (0.05 + (1 - 0.6) / (0.7 + 0.1))
    expected_principle = max(0.0, min(1.0, expected_principle))
    expected_residual = 0.5 * 0.8 + 0.5 * (0.8 - 0.7)
    expected_residual = max(0.0, min(1.0, expected_residual))

    assert math.isclose(res["adaptation_effectiveness"], expected_adaptation)
    assert math.isclose(res["principle_preservation"], expected_principle)
    assert math.isclose(res["residual_risk"], expected_residual)


def test_clamping() -> None:
    engine = CulturalSynthesisEngine()
    profile: CulturalProfile = {
        "clarity": 5.0,
        "foresight": 5.0,
        "empiricism": 5.0,
        "anchor_confidence": -5.0,
        "tri_score": -5.0,
        "layer_scores": {"x": 5.0},
    }
    res = engine.synthesize(profile)
    assert all(0.0 <= v <= 1.0 for v in res.values())
