"""Fidelity weighting helpers for Slot 02."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Tuple

from prometheus_client import Counter, Gauge

from nova.metrics.registry import REGISTRY
from nova.slots.slot01_truth_anchor.quantum_entropy import (
    EntropySample,
    get_entropy_sample,
)

from .config import FidelityWeightingConfig

_weight_gauge = Gauge(
    "slot2_fidelity_weight_applied",
    "Latest fidelity weighting factor applied to ΔTHRESH decisions",
    registry=REGISTRY,
)

_weight_events = Counter(
    "slot2_fidelity_weighting_events_total",
    "Total fidelity weighting computations performed by Slot02",
    ["source"],
    registry=REGISTRY,
)


class FidelityWeightingService:
    """Compute modulation weights based on Slot01 entropy fidelity."""

    def __init__(self, config: FidelityWeightingConfig) -> None:
        self.config = config

    def compute_weight(self) -> Tuple[float, Optional[EntropySample]]:
        if not self.config.enabled:
            return 1.0, None

        sample = get_entropy_sample(self.config.sample_bytes)
        fidelity = sample.fidelity if sample.fidelity is not None else self.config.reference
        weight = self._weight_from_fidelity(fidelity)
        _weight_gauge.set(weight)
        _weight_events.labels(source=sample.source or "unknown").inc()
        return weight, sample

    def _weight_from_fidelity(self, fidelity: float) -> float:
        weight = self.config.base + self.config.slope * (fidelity - self.config.reference)
        weight = max(self.config.clamp_lo, min(self.config.clamp_hi, weight))
        return weight


__all__ = ["FidelityWeightingService"]
