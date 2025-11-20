"""Temporal metrics for Phase-6 readiness."""

from __future__ import annotations

from prometheus_client import Gauge

from orchestrator.prometheus.public_registry import nova_public_registry
from orchestrator.prometheus.internal_registry import nova_internal_registry

temporal_drift_gauge = Gauge(
    "nova_temporal_drift",
    "Temporal drift between successive TRI coherence readings",
    registry=nova_internal_registry,
)
temporal_variance_gauge = Gauge(
    "nova_temporal_variance",
    "Variance of recent TRI coherence values",
    registry=nova_internal_registry,
)
temporal_prediction_error_gauge = Gauge(
    "nova_temporal_prediction_error",
    "Prediction error between expected and observed coherence",
    registry=nova_internal_registry,
)
temporal_convergence_gauge = Gauge(
    "nova_temporal_convergence",
    "Temporal convergence score",
    registry=nova_internal_registry,
)
temporal_snapshot_timestamp_gauge = Gauge(
    "nova_temporal_snapshot_timestamp",
    "Timestamp of last temporal snapshot (epoch seconds)",
    registry=nova_internal_registry,
)
temporal_router_state_gauge = Gauge(
    "nova_temporal_router_state",
    "Router temporal readiness (public-safe)",
    registry=nova_public_registry,
)


def record_temporal_metrics(snapshot) -> None:
    """Update temporal metrics from snapshot."""
    temporal_drift_gauge.set(snapshot.temporal_drift)
    temporal_variance_gauge.set(snapshot.temporal_variance)
    temporal_prediction_error_gauge.set(snapshot.prediction_error)
    temporal_convergence_gauge.set(snapshot.convergence_score)
    temporal_snapshot_timestamp_gauge.set(snapshot.timestamp)
    temporal_router_state_gauge.set(1.0 if snapshot.gate_state else 0.0)
