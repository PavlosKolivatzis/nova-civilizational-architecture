import threading
from typing import Dict, Optional

from prometheus_client import CollectorRegistry, Counter, Gauge, Histogram, Info

_registry: Optional[CollectorRegistry] = None
_lock = threading.Lock()
_metrics: Dict[str, object] = {}


def get_registry() -> CollectorRegistry:
    """Return the singleton CollectorRegistry for federation metrics."""
    global _registry
    with _lock:
        if _registry is None:
            _registry = CollectorRegistry(auto_describe=True)
        return _registry


def m() -> Dict[str, object]:
    """Lazily construct and cache federation metric handles."""
    if _metrics:
        return _metrics

    registry = get_registry()
    # Remove legacy gauge from registry when upgrading from previous releases
    try:
        legacy = registry._names_to_collectors["nova_federation_last_success_timestamp"]  # type: ignore[attr-defined]
        registry.unregister(legacy)
    except Exception:
        pass

    peers = Gauge(
        "nova_federation_peers",
        "Current peer count",
        registry=registry,
    )
    height = Gauge(
        "nova_federation_checkpoint_height",
        "Latest verified checkpoint height",
        registry=registry,
    )
    last_result_ts = Gauge(
        "nova_federation_last_result_timestamp",
        "Unix timestamp of last federation pull result by status",
        ("status",),
        registry=registry,
    )
    peer_up = Gauge(
        "nova_federation_peer_up",
        "Peer liveness (1=up, 0=missing)",
        ("peer",),
        registry=registry,
    )
    peer_last_seen = Gauge(
        "nova_federation_peer_last_seen",
        "Unix timestamp of last successful poll per peer",
        ("peer",),
        registry=registry,
    )
    peer_quality = Gauge(
        "nova_federation_peer_quality",
        "Composite peer quality score (0-1)",
        ("peer",),
        registry=registry,
    )
    peer_p95 = Gauge(
        "nova_federation_peer_last_p95_seconds",
        "Rolling p95 latency in seconds per peer",
        ("peer",),
        registry=registry,
    )
    peer_success = Gauge(
        "nova_federation_peer_success_rate",
        "Rolling success rate (0-1) per peer",
        ("peer",),
        registry=registry,
    )
    pull_seconds = Histogram(
        "nova_federation_pull_seconds",
        "Federation pull duration seconds",
        buckets=(0.05, 0.1, 0.25, 0.5, 1, 2, 5, 10),
        registry=registry,
    )
    pull_result = Counter(
        "nova_federation_pull_result_total",
        "Federation pull results by status",
        labelnames=("status",),
        registry=registry,
    )
    ready = Gauge(
        "nova_federation_ready",
        "1 when federation poller reports healthy readiness",
        registry=registry,
    )
    remediation_events = Counter(
        "nova_federation_remediation_events_total",
        "Auto-remediation events by reason",
        labelnames=("reason",),
        registry=registry,
    )
    remediation_last_action = Gauge(
        "nova_federation_remediation_last_action_timestamp",
        "Unix timestamp of the last federation remediation action",
        registry=registry,
    )
    remediation_backoff = Gauge(
        "nova_federation_backoff_seconds",
        "Current federation poll interval after backoff adjustments",
        registry=registry,
    )
    remediation_last_event = Info(
        "nova_federation_remediation_last_event",
        "Information about the most recent remediation action",
        registry=registry,
    )
    ledger_height = Gauge(
        "nova_ledger_height",
        "Current ledger checkpoint height",
        registry=registry,
    )
    ledger_head_age = Gauge(
        "nova_ledger_head_age_seconds",
        "Age of ledger head in seconds",
        registry=registry,
    )
    ledger_federation_gap = Gauge(
        "nova_ledger_federation_gap",
        "Signed difference: federation checkpoint height - ledger height",
        registry=registry,
    )
    ledger_federation_gap_abs = Gauge(
        "nova_ledger_federation_gap_abs",
        "Absolute gap between federation and ledger heights",
        registry=registry,
    )

    _metrics.update(
        {
            "peers": peers,
            "height": height,
            "last_result_ts": last_result_ts,
            "peer_up": peer_up,
            "peer_last_seen": peer_last_seen,
            "peer_quality": peer_quality,
            "peer_p95": peer_p95,
            "peer_success": peer_success,
            "pull_seconds": pull_seconds,
            "pull_result": pull_result,
            "ready": ready,
            "remediation_events": remediation_events,
            "remediation_last_action": remediation_last_action,
            "remediation_backoff": remediation_backoff,
            "remediation_last_event": remediation_last_event,
            "ledger_height": ledger_height,
            "ledger_head_age": ledger_head_age,
            "ledger_federation_gap": ledger_federation_gap,
            "ledger_federation_gap_abs": ledger_federation_gap_abs,
        }
    )
    # Ensure gauges have an explicit sample on startup
    last_result_ts.labels(status="success").set(0.0)
    last_result_ts.labels(status="error").set(0.0)
    ready.set(0.0)
    remediation_last_action.set(0.0)
    remediation_backoff.set(0.0)
    remediation_last_event.info({"reason": "none", "interval": "0", "timestamp": "0"})
    ledger_height.set(0)
    ledger_head_age.set(0.0)
    ledger_federation_gap.set(0)
    ledger_federation_gap_abs.set(0)
    return _metrics
