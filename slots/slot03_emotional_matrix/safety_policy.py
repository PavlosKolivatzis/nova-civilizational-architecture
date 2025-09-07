"""Safety policies for Emotional Matrix output.

Provides simple hooks that can be attached to the EmotionalMatrixEngine
via configuration. Policies operate in-place on the metrics dict and
should avoid raising exceptions.
"""
from __future__ import annotations

from typing import Dict

_ALLOWED_TONES = {"positive", "negative", "neutral", "unknown"}


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
    if not isinstance(score, (int, float)):
        metrics["score"] = 0.0
    else:
        metrics["score"] = float(max(-1.0, min(1.0, score)))
