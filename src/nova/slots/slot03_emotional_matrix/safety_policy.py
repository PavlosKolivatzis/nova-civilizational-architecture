"""Safety policies for Emotional Matrix output.

Provides simple hooks that can be attached to the EmotionalMatrixEngine
via configuration. Policies operate in-place on the metrics dict and
should avoid raising exceptions.
"""
from __future__ import annotations

from typing import Dict

ALLOWED_TONES = {"positive", "negative", "neutral", "unknown", "joy", "sadness", "anger", "fear", "surprise", "disgust", "dormant"}

def validate_metrics(metrics: dict) -> list[str]:
    """Validate metrics and return list of error codes."""
    errors: list[str] = []

    tone = metrics.get("emotional_tone")
    if tone not in ALLOWED_TONES:
        errors.append("invalid_tone")

    conf = metrics.get("confidence", 0.0)
    try:
        c = float(conf)
    except Exception:
        errors.append("confidence_out_of_bounds")
    else:
        if not (0.0 <= c <= 1.0):
            errors.append("confidence_out_of_bounds")

    # Check score bounds
    score = metrics.get("score")
    if score is not None:
        try:
            s = float(score)
            if not (-1.0 <= s <= 1.0):
                errors.append("score_out_of_bounds")
        except Exception:
            errors.append("score_out_of_bounds")

    return errors
_ALLOWED_TONES = {"positive", "negative", "neutral", "unknown", "dormant"}


def basic_safety_policy(metrics: Dict) -> None:
    """Clamp score range and validate tone label.

    This function demonstrates how safety hooks can post-process the
    analysis metrics without modifying core engine logic. It is purposely
    lightweight but easily replaceable with more sophisticated policies.
    """
    tone = metrics.get("emotional_tone")
    if tone not in _ALLOWED_TONES:
        metrics["policy_warning"] = f"invalid tone: {tone}"
        metrics["emotional_tone"] = "neutral"

    score = metrics.get("score", 0.0)
    # Phase 14.4: Preserve None for VOID dormancy (epistemic null)
    if score is None:
        pass  # VOID dormancy: keep None (not 0.0)
    elif not isinstance(score, (int, float)):
        metrics["score"] = 0.0
    else:
        metrics["score"] = float(max(-1.0, min(1.0, score)))
