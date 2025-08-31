from adaptive_synthesis_engine import AdaptiveSynthesisEngine, SimulationResult
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

