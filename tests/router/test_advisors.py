from orchestrator.router.advisors.slot05 import score_slot05
from orchestrator.router.advisors.slot08 import score_slot08


def test_slot05_advisor_uses_request_override():
    score = score_slot05({"slot05_alignment": 0.9})
    assert score.name == "slot05"
    assert score.score == 0.9


def test_slot08_advisor_clamps_values():
    score = score_slot08({"slot08_continuity": 1.5})
    assert score.score == 1.0
