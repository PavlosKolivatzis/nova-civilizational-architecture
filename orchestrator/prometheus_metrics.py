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

# --- LightClock & System Health metrics ------------------------------------
lightclock_phase_lock_gauge = Gauge(
    "nova_lightclock_phase_lock",
    "Current LightClock phase lock value from Slot3",
    registry=_REGISTRY,
)

system_pressure_gauge = Gauge(
    "nova_system_pressure_level",
    "System pressure level from Slot7",
    registry=_REGISTRY,
)

tri_coherence_gauge = Gauge(
    "nova_tri_coherence",
    "TRI signal coherence from Slot4",
    registry=_REGISTRY,
)

deployment_gate_gauge = Gauge(
    "nova_deployment_gate_open",
    "Whether Slot10 deployment gate is open (1=open, 0=closed)",
    registry=_REGISTRY,
)

semantic_mirror_ops_counter = Gauge(
    "nova_semantic_mirror_operations_total",
    "Total semantic mirror operations",
    ["operation_type"],
    registry=_REGISTRY,
)

# Reciprocal Contextual Unlearning metrics
unlearn_pulses_sent_gauge = Gauge(
    "nova_unlearn_pulses_sent_total",
    "Total unlearn pulses sent on context expiration",
    registry=_REGISTRY,
)

entries_expired_gauge = Gauge(
    "nova_entries_expired_total",
    "Total context entries expired from semantic mirror",
    registry=_REGISTRY,
)

unlearn_pulse_destinations_gauge = Gauge(
    "nova_unlearn_pulse_to_slot_total",
    "Unlearn pulses sent to specific slots",
    ["slot"],
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


def update_lightclock_metrics() -> None:
    """Update LightClock phase lock metrics from Slot3."""
    try:
        from orchestrator.semantic_mirror import get_semantic_mirror
        mirror = get_semantic_mirror()
        if mirror:
            phase_lock = mirror.get_context("slot03.phase_lock", "prometheus_metrics")
            if phase_lock is not None:
                lightclock_phase_lock_gauge.set(float(phase_lock))
                return

        # Fallback: try environment variable
        from os import getenv
        env_phase_lock = getenv("SLOT03_PHASE_LOCK")
        if env_phase_lock:
            lightclock_phase_lock_gauge.set(float(env_phase_lock))
        else:
            # Default phase lock value when no data available
            lightclock_phase_lock_gauge.set(0.5)
    except Exception:
        lightclock_phase_lock_gauge.set(0.5)  # Conservative default


def update_semantic_mirror_metrics() -> None:
    """Update semantic mirror and unlearn pulse metrics."""
    try:
        from orchestrator.semantic_mirror import get_semantic_mirror
        mirror = get_semantic_mirror()

        if mirror and hasattr(mirror, '_metrics'):
            # Update unlearn pulse metrics
            unlearn_sent = mirror._metrics.get("unlearn_pulses_sent", 0)
            unlearn_pulses_sent_gauge.set(unlearn_sent)

            expired = mirror._metrics.get("entries_expired", 0)
            entries_expired_gauge.set(expired)

            # Update per-slot pulse metrics
            for key, value in mirror._metrics.items():
                if key.startswith("unlearn_pulse_to_"):
                    slot = key.replace("unlearn_pulse_to_", "")
                    unlearn_pulse_destinations_gauge.labels(slot=slot).set(value)

    except Exception:
        pass  # Safe fallback - metrics remain unchanged


def update_system_health_metrics() -> None:
    """Update system pressure, TRI coherence, and deployment gate status."""
    from os import getenv

    try:
        from orchestrator.semantic_mirror import get_semantic_mirror
        mirror = get_semantic_mirror()

        # System pressure from Slot7 (with env fallback)
        pressure = None
        if mirror:
            pressure = mirror.get_context("slot07.pressure_level", "prometheus_metrics")
        if pressure is None:
            pressure = getenv("SLOT07_PRESSURE_LEVEL", "0.3")  # Default low pressure
        system_pressure_gauge.set(float(pressure))

        # TRI coherence from Slot4 (with env fallback)
        coherence = None
        if mirror:
            coherence = mirror.get_context("slot04.coherence", "prometheus_metrics")
        if coherence is None:
            coherence = getenv("TRI_COHERENCE", "0.7")  # Default decent coherence
        tri_coherence_gauge.set(float(coherence))

        # Deployment gate status - always compute even with defaults
        try:
            from slots.slot10_civilizational_deployment.core.lightclock_gatekeeper import LightClockGatekeeper
            gatekeeper = LightClockGatekeeper(mirror=mirror)
            gate_open = gatekeeper.should_open_gate()
            deployment_gate_gauge.set(1 if gate_open else 0)
        except Exception:
            deployment_gate_gauge.set(0)  # Conservative: gate closed on error

    except Exception:
        # Complete fallback - set reasonable defaults
        system_pressure_gauge.set(0.3)
        tri_coherence_gauge.set(0.7)
        deployment_gate_gauge.set(0)


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
    update_lightclock_metrics()
    update_system_health_metrics()
    update_semantic_mirror_metrics()
    return generate_latest(_REGISTRY), CONTENT_TYPE_LATEST