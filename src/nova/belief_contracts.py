"""Phase 6.0 Probabilistic Contracts for Nova Civilizational Architecture.

Implements Bayesian belief propagation for uncertainty quantification in
cross-slot communication, enabling graceful degradation during mirror outages.
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class BeliefState:
    """Represents a probabilistic belief with uncertainty bounds."""
    mean: float
    variance: float
    timestamp: float
    confidence: float = 1.0  # Derived: 1.0 - variance (normalized)

    def __post_init__(self):
        # Normalize confidence to [0,1]
        object.__setattr__(self, 'confidence', max(0.0, min(1.0, 1.0 - self.variance)))

    @classmethod
    def from_point_estimate(cls, value: float, uncertainty: float = 0.01) -> BeliefState:
        """Create belief from deterministic value with minimal uncertainty."""
        return cls(mean=value, variance=uncertainty, timestamp=time.time())

    def decayed(self, time_since_update: float, decay_rate: float = 0.1) -> BeliefState:
        """Return belief with increased variance due to staleness."""
        # Exponential variance growth with time
        decay_factor = 1.0 + decay_rate * time_since_update
        new_variance = min(1.0, self.variance * decay_factor)
        return BeliefState(
            mean=self.mean,
            variance=new_variance,
            timestamp=self.timestamp
        )


def update_belief(prior: BeliefState, likelihood: BeliefState) -> BeliefState:
    """Bayesian conjugate update for Gaussian beliefs (precision-weighted average)."""
    if prior.variance == 0.0:
        # Infinite precision prior - no update
        return prior
    if likelihood.variance == 0.0:
        # Infinite precision likelihood - adopt it
        return likelihood

    # Precision-weighted update (conjugate prior for Gaussian)
    prior_precision = 1.0 / prior.variance
    likelihood_precision = 1.0 / likelihood.variance

    posterior_precision = prior_precision + likelihood_precision
    posterior_mean = (
        (prior.mean * prior_precision + likelihood.mean * likelihood_precision)
        / posterior_precision
    )
    posterior_variance = 1.0 / posterior_precision

    return BeliefState(
        mean=posterior_mean,
        variance=posterior_variance,
        timestamp=max(prior.timestamp, likelihood.timestamp)
    )


def fuse_beliefs(beliefs: list[BeliefState]) -> Optional[BeliefState]:
    """Fuse multiple beliefs using precision weighting."""
    if not beliefs:
        return None

    valid_beliefs = [b for b in beliefs if b.variance < 1.0]  # Filter degraded beliefs
    if not valid_beliefs:
        return None

    # Sequential fusion
    fused = valid_beliefs[0]
    for belief in valid_beliefs[1:]:
        fused = update_belief(fused, belief)

    return fused