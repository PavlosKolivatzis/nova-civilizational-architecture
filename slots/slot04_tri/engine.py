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
import re
from functools import lru_cache


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


def _word_count_fast(text: str) -> int:
    return 1 + text.count(" ") if text else 0


_ABS = re.compile(r"\b(always|never|everyone|nobody|undeniably|absolutely|certainly)\b", re.I)
_HUM = re.compile(r"\b(may|might|could|appears|suggests|evidence|source|study|data|research)\b", re.I)
_UNC = re.compile(r"\b(uncertain|unclear|unknown|possibly|perhaps|seems)\b", re.I)
_LAYER_PATTERNS: Dict[str, List[re.Pattern]] = {
    "delta": [
        re.compile(r"\bundeniable\s+truth\b", re.I),
        re.compile(r"\bcannot\s+be\s+(?:questioned|disputed|denied)\b", re.I),
        re.compile(r"\bself-evident\s+(?:truth|fact)\b", re.I),
    ],
    "sigma": [
        re.compile(r"\bofficial\s+(?:statement|position|policy)\b", re.I),
        re.compile(r"\bauthoritative\s+(?:source|voice|guidance)\b", re.I),
    ],
    "theta": [
        re.compile(r"\bas\s+(?:proven|established)\s+(?:above|earlier)\b", re.I),
        re.compile(r"\bthis\s+(?:proves|validates)\s+our\s+(?:point|claim)\b", re.I),
    ],
    "omega": [
        re.compile(r"\beveryone\s+(?:knows|agrees|believes)\b", re.I),
        re.compile(r"\bwidely\s+(?:accepted|believed|known)\b", re.I),
        re.compile(r"\bviral\s+truth\b", re.I),
    ],
}


class TRIEngine:
    """Truth Resonance Index computation engine.

    The engine maintains per-trace Bayesian statistics and applies a
    Kalman filter to smooth TRI estimates over time. It supports
    integration with the IDS subsystem via ``calculate_base_score``,
    ``get_previous_vector`` and ``store_vector`` methods.
    """

    VERSION = "0.1.0"

    def __init__(self, process_variance: float = 0.01, ewma_alpha: float = 0.2) -> None:
        self.process_variance = float(process_variance)
        self._status: Dict[Tuple[str, str], TRIStatus] = {}
        self._alpha = ewma_alpha
        self._ewma = 0.7
        self._calc_cached = lru_cache(maxsize=4096)(self._calc_impl)

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
    # Text TRI scoring
    # ------------------------------------------------------------------
    def _layer_score(self, text: str, patterns: List[re.Pattern]) -> float:
        hits = 0
        for p in patterns:
            if p.search(text):
                hits += 1
        return hits / max(1, len(patterns))

    def _base_tri(self, text: str) -> float:
        words = max(1, _word_count_fast(text))
        penalty = min(0.4, (len(_ABS.findall(text)) / words) * 2.0)
        bonus_h = min(0.3, (len(_HUM.findall(text)) / words) * 1.5)
        bonus_u = min(0.2, (len(_UNC.findall(text)) / words) * 1.0)
        return max(0.0, min(1.0, 0.7 - penalty + bonus_h + bonus_u))

    def _calc_impl(self, text: str) -> dict:
        layers = {k: self._layer_score(text, v) for k, v in _LAYER_PATTERNS.items()}
        tri = self._base_tri(text)
        self._ewma = self._alpha * tri + (1 - self._alpha) * self._ewma
        return {"score": tri, "smoothed": self._ewma, "layer_scores": layers}

    def calculate(self, text: str) -> dict:
        return dict(self._calc_cached(text))

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


__all__ = ["TRIEngine", "TRIStatus"]
