from slots.slot03_emotional_matrix.emotional_matrix_engine import EmotionalMatrixEngine, EmotionConfig
from slots.slot03_emotional_matrix.safety_policy import basic_safety_policy
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


def test_extended_lexicon_tokens() -> None:
    engine = EmotionalMatrixEngine()
    pos = engine.analyze("The meal was delightful")
    neg = engine.analyze("The experience was dreadful")
    assert pos["emotional_tone"] == "positive"
    assert neg["emotional_tone"] == "negative"


def test_configurable_policy_hooks() -> None:
    called = []

    def hook(metrics):
        metrics["hooked"] = True
        called.append(True)

    engine = EmotionalMatrixEngine(EmotionConfig(policy_hooks=[hook]))
    res = engine.analyze("good")
    assert called
    assert res.get("hooked") is True


def test_safety_policy_module() -> None:
    metrics = {"emotional_tone": "weird", "score": 5}
    basic_safety_policy(metrics)
    assert metrics["emotional_tone"] == "neutral"
    assert metrics["score"] == 1.0
    assert "policy_warning" in metrics


def test_booster_with_negation() -> None:
    engine = EmotionalMatrixEngine()
    # Booster "very" increases positivity, but preceding negation should flip it
    res = engine.analyze("not very good")
    assert res["score"] <= 0
    assert res["emotional_tone"] in {"negative", "neutral"}


def test_phase_lock_dampens_score(monkeypatch) -> None:
    """Test that low phase_lock dampens emotional intensity."""
    import os
    monkeypatch.setenv("SLOT07_PHASE_LOCK", "0.4")
    monkeypatch.setenv("NOVA_LIGHTCLOCK_DEEP", "1")

    engine = EmotionalMatrixEngine()
    res = engine.analyze("This is very fantastic and awesome!")

    # Score should be dampened (20% reduction) and positive
    assert res["score"] > 0  # Should be positive
    assert res["score"] <= 0.8  # But dampened
    assert "annotations" in res
    assert res["annotations"]["phase_lock"] == 0.4
    assert res["annotations"]["lightclock_adjustment"] == "dampened_20pct"


def test_phase_lock_no_effect_when_high(monkeypatch) -> None:
    """Test that high phase_lock doesn't dampen emotions."""
    import os
    monkeypatch.setenv("SLOT07_PHASE_LOCK", "0.8")
    monkeypatch.setenv("NOVA_LIGHTCLOCK_DEEP", "1")

    engine = EmotionalMatrixEngine()
    res = engine.analyze("This is very fantastic and awesome!")

    # No dampening should occur
    assert "annotations" not in res or "lightclock_adjustment" not in res.get("annotations", {})


def test_phase_lock_disabled_by_flag(monkeypatch) -> None:
    """Test that NOVA_LIGHTCLOCK_DEEP=0 disables phase_lock."""
    import os
    monkeypatch.setenv("SLOT07_PHASE_LOCK", "0.3")
    monkeypatch.setenv("NOVA_LIGHTCLOCK_DEEP", "0")

    engine = EmotionalMatrixEngine()
    res = engine.analyze("This is VERY EXCITING!!!")

    # No dampening should occur when disabled
    assert "annotations" not in res or "lightclock_adjustment" not in res.get("annotations", {})
