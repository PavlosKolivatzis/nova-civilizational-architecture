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

# Prometheus metrics (handle re-import gracefully for test isolation)
try:
    _weight_gauge = Gauge(
        "slot2_fidelity_weight_applied",
        "Latest fidelity weighting factor applied to ΔTHRESH decisions",
        registry=REGISTRY,
    )
except ValueError:
    # Metric already registered (e.g., in tests with multiple imports)
    _weight_gauge = REGISTRY._names_to_collectors.get("slot2_fidelity_weight_applied")

try:
    _weight_events = Counter(
        "slot2_fidelity_weighting_events_total",
        "Total fidelity weighting computations performed by Slot02",
        ["source"],
        registry=REGISTRY,
    )
except ValueError:
    # Metric already registered
    _weight_events = REGISTRY._names_to_collectors.get("slot2_fidelity_weighting_events_total")


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

        # Emit to ledger (Phase 13 RUN 13-3)
        self._emit_deltathresh_applied(fidelity, weight, sample)

        return weight, sample

    def _weight_from_fidelity(self, fidelity: float) -> float:
        weight = self.config.base + self.config.slope * (fidelity - self.config.reference)
        weight = max(self.config.clamp_lo, min(self.config.clamp_hi, weight))
        return weight

    def _emit_deltathresh_applied(
        self, fidelity: float, weight: float, sample: Optional[EntropySample]
    ) -> None:
        """Emit DELTATHRESH_APPLIED event to ledger."""
        try:
            from nova.ledger.client import LedgerClient
            from nova.ledger.model import RecordKind

            client = LedgerClient.get_instance()
            anchor_id = f"slot02-fidelity-{sample.digest()[:16] if sample else 'unknown'}"

            client.append_record(
                anchor_id=anchor_id,
                slot="02",
                kind=RecordKind.DELTATHRESH_APPLIED,
                payload={
                    "fidelity": fidelity,
                    "weight": weight,
                    "entropy_source": sample.source if sample else None,
                    "entropy_backend": sample.backend if sample else None,
                    "entropy_sha3_256": sample.digest() if sample else None,
                },
                producer="slot02",
                version="1.0.0",
            )
        except Exception:
            # Don't fail processing if ledger emission fails
            pass


__all__ = ["FidelityWeightingService"]
