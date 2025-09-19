"""Prometheus metrics export for Nova system."""

from prometheus_client import (
    Gauge,
    generate_latest,
    CONTENT_TYPE_LATEST,
    CollectorRegistry,
)
from orchestrator.metrics import get_slot6_metrics
from os import getenv

# Dedicated registry (avoids duplicate registration across tests/imports)
_REGISTRY = CollectorRegistry()

# Prometheus gauges
slot6_p95_residual_risk_gauge = Gauge(
    "nova_slot6_p95_residual_risk",
    "Slot6 95th percentile residual risk from cultural synthesis decisions",
    ["slot"],
    registry=_REGISTRY,
)

# --- Flag gauges (Phase 2 feature flags) ------------------------------------
def _env_truthy(name: str) -> bool:
    v = (getenv(name, "") or "").strip().lower()
    return v in {"1", "true", "yes", "on"}

# One gauge, labeled by flag name
feature_flag_gauge = Gauge(
    "nova_feature_flag_enabled",
    "Nova Phase-2 feature flag states",
    ["flag"],
    registry=_REGISTRY,
)

# --- Slot1 Truth Anchor metrics ------------------------------------
slot1_anchors_gauge = Gauge(
    "nova_slot1_anchors_total",
    "Total number of truth anchors registered",
    registry=_REGISTRY,
)

slot1_lookups_counter = Gauge(
    "nova_slot1_lookups_total",
    "Total number of anchor lookups performed",
    registry=_REGISTRY,
)

slot1_recoveries_counter = Gauge(
    "nova_slot1_recoveries_total",
    "Total number of successful anchor recoveries",
    registry=_REGISTRY,
)

slot1_failures_counter = Gauge(
    "nova_slot1_failures_total",
    "Total number of anchor verification failures",
    registry=_REGISTRY,
)


def update_slot6_metrics():
    """Update Slot6 metrics for Prometheus export."""
    s6_metrics = get_slot6_metrics().get_metrics()
    p95 = s6_metrics.get("p95_residual_risk")

    if p95 is not None:
        slot6_p95_residual_risk_gauge.labels(slot="6").set(p95)
    else:
        # Avoid stale sample if window empties / not yet primed
        try:
            slot6_p95_residual_risk_gauge.remove("6")
        except KeyError:
            pass


def update_flag_metrics() -> None:
    """Update feature flag metrics for Prometheus export."""
    # Import inside function to avoid hard import at module import time
    try:
        from slots.slot07_production_controls.flag_metrics import get_flag_state_metrics
        flags = get_flag_state_metrics()
        tri_on   = bool(flags.get("tri_link_enabled", False))
        life_on  = bool(flags.get("lifespan_enabled", False))
        hash_on  = bool(flags.get("shared_hash_enabled", False))
    except Exception:
        # Fallback purely to env (keeps metrics usable even if Slot7 is unavailable)
        tri_on  = _env_truthy("NOVA_ENABLE_TRI_LINK")
        life_on = _env_truthy("NOVA_ENABLE_LIFESPAN")
        hash_on = _env_truthy("NOVA_USE_SHARED_HASH")

    prom_on = _env_truthy("NOVA_ENABLE_PROMETHEUS")

    feature_flag_gauge.labels(flag="NOVA_ENABLE_TRI_LINK").set(1 if tri_on else 0)
    feature_flag_gauge.labels(flag="NOVA_ENABLE_LIFESPAN").set(1 if life_on else 0)
    feature_flag_gauge.labels(flag="NOVA_USE_SHARED_HASH").set(1 if hash_on else 0)
    feature_flag_gauge.labels(flag="NOVA_ENABLE_PROMETHEUS").set(1 if prom_on else 0)


def update_slot1_metrics() -> None:
    """Update Slot1 truth anchor metrics for Prometheus export."""
    try:
        from orchestrator.adapters.slot1_truth_anchor import Slot1TruthAnchorAdapter
        adapter = Slot1TruthAnchorAdapter()

        if adapter.available:
            snapshot = adapter.snapshot()
            slot1_anchors_gauge.set(snapshot.get("anchors", 0))
            slot1_lookups_counter.set(snapshot.get("lookups", 0))
            slot1_recoveries_counter.set(snapshot.get("recoveries", 0))
            slot1_failures_counter.set(snapshot.get("failures", 0))
        else:
            # Clear metrics if Slot1 not available
            slot1_anchors_gauge.set(0)
            slot1_lookups_counter.set(0)
            slot1_recoveries_counter.set(0)
            slot1_failures_counter.set(0)
    except Exception:
        # Fallback - set all to 0 if Slot1 unavailable
        slot1_anchors_gauge.set(0)
        slot1_lookups_counter.set(0)
        slot1_recoveries_counter.set(0)
        slot1_failures_counter.set(0)


def get_metrics_response():
    """Get Prometheus metrics response."""
    update_slot6_metrics()
    update_flag_metrics()
    update_slot1_metrics()
    return generate_latest(_REGISTRY), CONTENT_TYPE_LATEST