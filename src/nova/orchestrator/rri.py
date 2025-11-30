"""Reflective Resonance Index helpers with short-term smoothing."""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from time import monotonic
from typing import Deque, Tuple

from prometheus_client import Counter, Gauge

from nova.orchestrator.prometheus_metrics import _REGISTRY

# Prometheus primitives -------------------------------------------------------
RRI_GAUGE = Gauge(
    "nova_reflective_resonance_index",
    "Composite 0..1 score for reflective resonance (5m window)",
    registry=_REGISTRY,
)
REFLECT_TRACES = Counter(
    "nova_reflect_traces_total",
    "Total reflective trace events observed",
    registry=_REGISTRY,
)
ETHICS_FORECASTS = Counter(
    "nova_ethics_forecasts_total",
    "Total ethics forecast events observed",
    registry=_REGISTRY,
)
COUNTERFACTUALS = Counter(
    "nova_counterfactuals_total",
    "Total counterfactual sampling events observed",
    registry=_REGISTRY,
)


WINDOW_SECONDS = 300.0


@dataclass
class _WindowSample:
    timestamp: float
    total: float
    reflect: float
    forecast: float
    counterfactual: float


_history: Deque[_WindowSample] = deque()
_last_counts: Tuple[float, float, float, float] | None = None


def reset() -> None:
    """Reset window history (primarily used in tests)."""
    _history.clear()
    global _last_counts
    _last_counts = None
    RRI_GAUGE.set(0.0)


def _append_sample(total: float, reflect: float, forecast: float, counter: float, *, ts: float) -> None:
    _history.append(_WindowSample(ts, total, reflect, forecast, counter))
    cutoff = ts - WINDOW_SECONDS
    while _history and _history[0].timestamp < cutoff:
        _history.popleft()


def _compute_ratio(weights: Tuple[float, float, float]) -> float:
    total = sum(sample.total for sample in _history)
    if total <= 0:
        return 0.0
    reflect_sum = sum(sample.reflect for sample in _history)
    forecast_sum = sum(sample.forecast for sample in _history)
    counter_sum = sum(sample.counterfactual for sample in _history)

    w_ref, w_forecast, w_counter = weights
    value = (
        w_ref * (reflect_sum / total)
        + w_forecast * (forecast_sum / total)
        + w_counter * (counter_sum / total)
    )
    return max(0.0, min(1.0, value))


def update_from_totals(
    total: float,
    reflect: float,
    forecast: float,
    counter: float,
    *,
    weights: Tuple[float, float, float] = (0.4, 0.4, 0.2),
    now: float | None = None,
) -> None:
    """Update the RRI gauge from monotonic cumulative totals."""
    ts = now if now is not None else monotonic()
    global _last_counts
    counts = (total, reflect, forecast, counter)

    if _last_counts is None:
        _last_counts = counts
        return

    prev_total, prev_reflect, prev_forecast, prev_counter = _last_counts
    delta_total = max(0.0, total - prev_total)
    delta_reflect = max(0.0, reflect - prev_reflect)
    delta_forecast = max(0.0, forecast - prev_forecast)
    delta_counter = max(0.0, counter - prev_counter)

    _append_sample(delta_total, delta_reflect, delta_forecast, delta_counter, ts=ts)
    _last_counts = counts

    ratio = _compute_ratio(weights)
    RRI_GAUGE.set(ratio)


__all__ = [
    "RRI_GAUGE",
    "REFLECT_TRACES",
    "ETHICS_FORECASTS",
    "COUNTERFACTUALS",
    "update_from_totals",
    "reset",
]
