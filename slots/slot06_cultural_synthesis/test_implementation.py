import json
from slot06_cultural_synthesis.multicultural_truth_synthesis import (
    AdaptiveSynthesisEngine,
    MulticulturalTruthSynthesisAdapter,
    SimulationResult,
)
def test_basic_approve():
    eng = AdaptiveSynthesisEngine()
    res = eng.analyze_and_simulate("Test", {"content": "perspective on global data"}, {"region": "EU", "educational_context": True})
    assert res.simulation_status in (SimulationResult.APPROVED, SimulationResult.APPROVED_WITH_TRANSFORMATION)
def test_forbidden_block():
    eng = AdaptiveSynthesisEngine()
    res = eng.analyze_and_simulate("Test", {"content": "guided by divine revelation only"}, {})
    assert res.simulation_status == SimulationResult.BLOCKED_BY_GUARDRAIL
    assert res.violations
def test_adapter():
    eng = AdaptiveSynthesisEngine()
    ad = MulticulturalTruthSynthesisAdapter(eng)
    prof = ad.analyze_cultural_context("Org", {"region": "US"})
    assert 0.0 <= prof.adaptation_effectiveness <= 1.0
