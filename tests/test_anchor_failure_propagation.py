from slots.slot06_cultural_synthesis.engine import AdaptiveSynthesisEngine, SimulationResult
import math


class StubEngine(AdaptiveSynthesisEngine):
    def __init__(self, anchor_result):
        super().__init__()
        self._stub_result = anchor_result

    def _verify_anchor_integrity(self, content: str):
        return self._stub_result


def test_violation_reduces_compliance_and_status():
    anchor_result = {
        "anchor_status": "VIOLATED",
        "anchor_confidence": 0.8,
        "anchor_verified": False,
        "anchor_violations": ["v"],
    }
    engine = StubEngine(anchor_result)
    result = engine.analyze_and_simulate("inst", {"content": "x"})
    assert result.simulation_status == SimulationResult.APPROVED_WITH_TRANSFORMATION
    assert result.compliance_score < 1.0
    assert math.isclose(result.compliance_score, 0.818, rel_tol=1e-3)


def test_failed_blocks_simulation():
    anchor_result = {
        "anchor_status": "FAILED",
        "anchor_confidence": 0.4,
        "anchor_verified": False,
        "anchor_violations": ["v"],
    }
    engine = StubEngine(anchor_result)
    result = engine.analyze_and_simulate("inst", {"content": "x"})
    assert result.simulation_status == SimulationResult.BLOCKED_BY_GUARDRAIL
    assert result.compliance_score == 0.0


def test_penalty_scales_with_confidence_and_truth_score():
    violating = {
        "anchor_status": "VIOLATED",
        "anchor_confidence": 0.6,
        "anchor_verified": False,
        "anchor_violations": ["v"],
    }
    baseline = {
        "anchor_status": "VERIFIED",
        "anchor_confidence": 1.0,
        "anchor_verified": True,
        "anchor_violations": [],
    }

    baseline_engine = StubEngine(baseline)
    baseline_result = baseline_engine.analyze_and_simulate("inst", {"content": "x"})

    engine = StubEngine(violating)
    result = engine.analyze_and_simulate("inst", {"content": "x"})

    expected_penalty = (1 - violating["anchor_confidence"]) / 1.1
    expected_score = 1 - expected_penalty

    assert result.simulation_status == SimulationResult.APPROVED_WITH_TRANSFORMATION
    assert math.isclose(result.compliance_score, expected_score, rel_tol=1e-3)
    assert math.isclose(
        result.cultural_profile.adaptation_effectiveness,
        baseline_result.cultural_profile.adaptation_effectiveness * expected_score,
        rel_tol=1e-3,
    )

