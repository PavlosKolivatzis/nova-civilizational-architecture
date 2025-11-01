import threading
from typing import Dict

from prometheus_client import CollectorRegistry, Counter, Gauge, Histogram

_registry: CollectorRegistry | None = None
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
    last_ts = Gauge(
        "nova_federation_last_success_timestamp",
        "Unix ts of last successful pull",
        registry=registry,
    )
    peer_up = Gauge(
        "nova_federation_peer_up",
        "Peer liveness (1=up, 0=missing)",
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

    _metrics.update(
        {
            "peers": peers,
            "height": height,
            "last_ts": last_ts,
            "peer_up": peer_up,
            "pull_seconds": pull_seconds,
            "pull_result": pull_result,
        }
    )
    return _metrics
