"""TRI Engine implementation for Slot 4.

Provides Truth Resonance Index (TRI) measurement combining a
Bayesian update over observed truth vectors with a simple 1D
Kalman filter for temporal smoothing. The engine exposes minimal
methods used by other slots and services.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
import math


@dataclass
class TRIStatus:
    """State for a tracked TRI sequence.

    Attributes
    ----------
    estimate:
        Current Kalman-filtered TRI estimate.
    variance:
        Variance associated with ``estimate``.
    alpha:
        Alpha parameter of the underlying Beta distribution.
    beta:
        Beta parameter of the underlying Beta distribution.
    confidence_interval:
        Tuple representing the 95% confidence interval for the
        estimate.
    last_vector:
        The most recent raw vector provided for this sequence.
    iterations:
        Number of updates performed for the sequence.
    """

    estimate: float
    variance: float
    alpha: float
    beta: float
    confidence_interval: Tuple[float, float]
    last_vector: List[float] = field(default_factory=list)
    iterations: int = 0


class TRIEngine:
    """Truth Resonance Index computation engine.

    The engine maintains per-trace Bayesian statistics and applies a
    Kalman filter to smooth TRI estimates over time. It supports
    integration with the IDS subsystem via ``calculate_base_score``,
    ``get_previous_vector`` and ``store_vector`` methods.
    """

    VERSION = "0.1.0"

    def __init__(self, process_variance: float = 0.01) -> None:
        self.process_variance = float(process_variance)
        self._status: Dict[Tuple[str, str], TRIStatus] = {}

    # ------------------------------------------------------------------
    # Basic scoring
    # ------------------------------------------------------------------
    def calculate_base_score(self, vector: List[float]) -> float:
        """Return a naive TRI score for ``vector``.

        Values are expected to be within ``[0, 1]`` and the result is
        simply the arithmetic mean clamped to that range. Used by
        upstream systems before IDS adjustments are applied.
        """
        if not vector:
            return 0.0
        cleaned = [max(0.0, min(1.0, float(v))) for v in vector]
        return sum(cleaned) / len(cleaned)

    # ------------------------------------------------------------------
    # State management helpers
    # ------------------------------------------------------------------
    def _key(self, trace_id: str, scope: str) -> Tuple[str, str]:
        return trace_id, scope

    def get_previous_vector(self, trace_id: str, scope: str = "traits") -> Optional[List[float]]:
        status = self._status.get(self._key(trace_id, scope))
        return list(status.last_vector) if status else None

    def store_vector(self, vector: List[float], trace_id: str, scope: str = "traits") -> TRIStatus:
        return self.update(vector, trace_id, scope)

    # ------------------------------------------------------------------
    # Core update logic
    # ------------------------------------------------------------------
    def update(self, vector: List[float], trace_id: str, scope: str = "traits") -> TRIStatus:
        """Update the TRI estimate for ``trace_id``/``scope``.

        A Bayesian update is performed on a Beta distribution representing
        the underlying truth probability. The resulting mean and
        variance become the observation for a Kalman filter step.
        """
        key = self._key(trace_id, scope)
        cleaned = [max(0.0, min(1.0, float(v))) for v in vector]
        successes = sum(cleaned)
        failures = len(cleaned) - successes

        prev = self._status.get(key)
        alpha_prior = prev.alpha if prev else 1.0
        beta_prior = prev.beta if prev else 1.0
        alpha_post = alpha_prior + successes
        beta_post = beta_prior + failures

        measurement = alpha_post / (alpha_post + beta_post)
        meas_var = (alpha_post * beta_post) / ((alpha_post + beta_post) ** 2 * (alpha_post + beta_post + 1))

        if prev:
            prior_est = prev.estimate
            prior_var = prev.variance + self.process_variance
            iterations = prev.iterations + 1
        else:
            prior_est = measurement
            prior_var = meas_var + self.process_variance
            iterations = 1

        kalman_gain = prior_var / (prior_var + meas_var)
        estimate = prior_est + kalman_gain * (measurement - prior_est)
        variance = (1 - kalman_gain) * prior_var

        std = math.sqrt(max(variance, 0.0))
        ci_low = max(0.0, estimate - 1.96 * std)
        ci_high = min(1.0, estimate + 1.96 * std)

        status = TRIStatus(
            estimate=estimate,
            variance=variance,
            alpha=alpha_post,
            beta=beta_post,
            confidence_interval=(ci_low, ci_high),
            last_vector=cleaned,
            iterations=iterations,
        )
        self._status[key] = status
        return status

    def get_status(self, trace_id: str, scope: str = "traits") -> Optional[TRIStatus]:
        """Return current :class:`TRIStatus` for ``trace_id`` and ``scope``."""
        return self._status.get(self._key(trace_id, scope))

    def calculate(self, content: str, context: Optional[Dict] = None) -> Dict:
        """High-level TRI calculation for plugin interface.

        Analyzes content and returns comprehensive TRI report with
        layer-by-layer analysis and confidence metrics.
        """
        if context is None:
            context = {}

        # Generate trace ID from content hash for consistency
        import hashlib
        trace_id = hashlib.sha256(content.encode()).hexdigest()[:16]

        # Extract feature vector from content (simplified implementation)
        vector = self._extract_features(content, context)

        # Update TRI state with new observation
        status = self.update(vector, trace_id, "analysis")

        # Calculate layer-specific scores
        layer_scores = self._analyze_layers(content, context)

        # Determine patterns detected
        patterns = self._detect_patterns(vector, content)

        # Prepare report with TRI metrics
        coherence = status.estimate  # Main TRI coherence score
        phase_coherence = min(1.0, status.estimate + 0.1)  # Slightly optimistic phase coherence
        phase_jitter = max(0.0, 1.0 - status.estimate)  # Inverse relationship with coherence

        report = {
            "tri_score": status.estimate,
            "coherence": coherence,
            "phase_coherence": phase_coherence,
            "phase_jitter": phase_jitter,
            "layer_scores": layer_scores,
            "confidence": self._calculate_confidence(status),
            "patterns": patterns,
            "trace_id": trace_id,
            "iterations": status.iterations,
            "confidence_interval": status.confidence_interval
        }

        # Publish TRI signals to Semantic Mirror (best-effort)
        try:
            from .publish import publish_tri_to_mirror
            publish_tri_to_mirror(coherence, phase_coherence, phase_jitter)
        except Exception:
            pass  # Never let mirror publishing break TRI processing

        return report

    def _extract_features(self, content: str, context: Dict) -> List[float]:
        """Extract numerical feature vector from content."""
        features = []

        # Basic content metrics (0-1 normalized)
        if content:
            # Length normalization (sigmoid)
            length_score = 2 / (1 + math.exp(-len(content) / 1000)) - 1
            features.append(max(0.0, min(1.0, length_score)))

            # Character diversity
            unique_chars = len(set(content.lower()))
            diversity_score = min(1.0, unique_chars / 26)  # Normalize by alphabet
            features.append(diversity_score)

            # Word-like structure
            words = content.split()
            if words:
                avg_word_len = sum(len(w) for w in words) / len(words)
                word_score = min(1.0, avg_word_len / 10)  # Reasonable word length
                features.append(word_score)
            else:
                features.append(0.0)

            # Punctuation ratio
            punct_count = sum(1 for c in content if not c.isalnum() and not c.isspace())
            punct_ratio = min(1.0, punct_count / max(1, len(content)))
            features.append(punct_ratio)
        else:
            features = [0.0, 0.0, 0.0, 0.0]

        # Context-based features
        if context.get("source_trusted", False):
            features.append(0.8)
        else:
            features.append(0.3)

        if context.get("verified", False):
            features.append(0.9)
        else:
            features.append(0.5)

        return features

    def _analyze_layers(self, content: str, context: Dict) -> Dict[str, float]:
        """Analyze content across different conceptual layers."""
        layers = {}

        # Syntactic layer - structure and format
        if content:
            # Check for balanced brackets, quotes, etc.
            brackets = content.count('(') + content.count('[') + content.count('{')
            brackets_close = content.count(')') + content.count(']') + content.count('}')
            balance_score = 1.0 - abs(brackets - brackets_close) / max(1, len(content))
            layers["syntactic"] = max(0.0, min(1.0, balance_score))
        else:
            layers["syntactic"] = 0.0

        # Semantic layer - meaning and coherence
        words = content.split() if content else []
        if len(words) > 2:
            # Simple coherence heuristic - repeated words indicate structure
            word_freq = {}
            for word in words:
                word_freq[word.lower()] = word_freq.get(word.lower(), 0) + 1

            repeated_words = sum(1 for count in word_freq.values() if count > 1)
            coherence_score = min(1.0, repeated_words / len(word_freq))
            layers["semantic"] = coherence_score
        else:
            layers["semantic"] = 0.3

        # Pragmatic layer - contextual appropriateness
        context_score = 0.5  # Default neutral
        if context.get("domain"):
            context_score += 0.2  # Has domain context
        if context.get("purpose"):
            context_score += 0.2  # Has purpose context
        layers["pragmatic"] = min(1.0, context_score)

        return layers

    def _detect_patterns(self, vector: List[float], content: str) -> List[str]:
        """Detect notable patterns in the analysis."""
        patterns = []

        # High confidence pattern
        if all(v > 0.7 for v in vector):
            patterns.append("high_confidence")

        # Low confidence pattern
        if all(v < 0.3 for v in vector):
            patterns.append("low_confidence")

        # Mixed signals
        high_count = sum(1 for v in vector if v > 0.7)
        low_count = sum(1 for v in vector if v < 0.3)
        if high_count > 0 and low_count > 0:
            patterns.append("mixed_signals")

        # Content-based patterns
        if content:
            if len(content) < 10:
                patterns.append("minimal_content")
            elif len(content) > 5000:
                patterns.append("extensive_content")

            if content.isupper():
                patterns.append("all_caps")
            elif content.islower():
                patterns.append("all_lowercase")

        return patterns

    def _calculate_confidence(self, status: TRIStatus) -> float:
        """Calculate overall confidence in the TRI estimate."""
        # Start with inverse of variance (more observations = higher confidence)
        base_confidence = 1.0 / (1.0 + status.variance)

        # Adjust based on number of iterations (more data = higher confidence)
        iteration_boost = min(0.3, status.iterations / 20)

        # Consider confidence interval width (narrower = higher confidence)
        ci_width = status.confidence_interval[1] - status.confidence_interval[0]
        ci_confidence = 1.0 - ci_width

        # Weighted combination
        confidence = (base_confidence * 0.5 +
                     (base_confidence + iteration_boost) * 0.3 +
                     ci_confidence * 0.2)

        return max(0.0, min(1.0, confidence))


__all__ = ["TRIEngine", "TRIStatus"]
