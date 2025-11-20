"""Temporal metrics stub."""

from __future__ import annotations

from prometheus_client import Gauge

from orchestrator.prometheus.public_registry import nova_public_registry

temporal_placeholder_gauge = Gauge(
    "nova_temporal_placeholder",
    "Placeholder metric for Phase-6 temporal scaffolding.",
    registry=nova_public_registry,
)


def record_placeholder(value: float = 0.0) -> None:
    temporal_placeholder_gauge.set(value)
