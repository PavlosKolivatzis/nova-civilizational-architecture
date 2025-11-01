import threading
from typing import Dict, Optional

from prometheus_client import CollectorRegistry, Counter, Gauge, Histogram

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

    _metrics.update(
        {
            "peers": peers,
            "height": height,
            "last_result_ts": last_result_ts,
            "peer_up": peer_up,
            "peer_last_seen": peer_last_seen,
            "pull_seconds": pull_seconds,
            "pull_result": pull_result,
            "ready": ready,
        }
    )
    # Ensure gauges have an explicit sample on startup
    last_result_ts.labels(status="success").set(0.0)
    last_result_ts.labels(status="error").set(0.0)
    ready.set(0.0)
    return _metrics
