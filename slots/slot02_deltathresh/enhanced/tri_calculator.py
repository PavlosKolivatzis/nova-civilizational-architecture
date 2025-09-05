"""Enhanced TRI calculation utilities."""

from __future__ import annotations

from .detector import EnhancedPatternDetector


def calculate_enhanced_tri_score(
    content: str, base_score: float, detector: EnhancedPatternDetector
) -> float:
    """Compute enhanced Truth Resonance Index score.

    Combines the base TRI score with contextual coherence signals.

    Args:
        content: Input text to evaluate.
        base_score: TRI score from the core processor.
        detector: Pattern detector providing contextual analysis.

    Returns:
        A TRI score normalized to the range [0.0, 1.0].
    """
    coherence = detector._contextual_consistency(content)
    return max(0.0, min(1.0, base_score + coherence * 0.05))
