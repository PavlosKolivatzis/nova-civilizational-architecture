from slots.slot03_emotional_matrix.emotional_matrix_engine import EmotionalMatrixEngine, EmotionConfig
import pytest


def test_positive_sentiment() -> None:
    engine = EmotionalMatrixEngine()
    res = engine.analyze("I feel great and fantastic")
    assert res["emotional_tone"] == "positive"
    assert res["confidence"] > 0


def test_negative_sentiment() -> None:
    engine = EmotionalMatrixEngine()
    res = engine.analyze("This is bad and awful")
    assert res["emotional_tone"] == "negative"
    assert res["confidence"] > 0


def test_neutral_sentiment() -> None:
    engine = EmotionalMatrixEngine()
    res = engine.analyze("This is a chair")
    assert res["emotional_tone"] == "neutral"


def test_negation_flips() -> None:
    engine = EmotionalMatrixEngine()
    res = engine.analyze("This is not good")
    assert res["emotional_tone"] in {"neutral", "negative"}  # not→good flips to non-positive
    # stronger check: score <= 0
    assert res["score"] <= 0


def test_intensifiers() -> None:
    engine = EmotionalMatrixEngine()
    a = engine.analyze("good")
    b = engine.analyze("very good")
    assert b["score"] >= a["score"]
    assert b["explain"]["matched"] >= 1


def test_policy_hook_failure_is_swallowed() -> None:
    engine = EmotionalMatrixEngine()

    def bad_hook(_):
        raise RuntimeError("boom")

    res = engine.analyze("good", policy_hook=bad_hook)
    assert res["emotional_tone"] == "positive"
    assert res.get("policy_error") == "policy hook failure"


def test_html_guard() -> None:
    engine = EmotionalMatrixEngine()
    with pytest.raises(ValueError):
        engine.analyze("<script>alert('x')</script>")


def test_length_guard() -> None:
    engine = EmotionalMatrixEngine(EmotionConfig(max_content_length=5))
    with pytest.raises(ValueError):
        engine.analyze("too long")
