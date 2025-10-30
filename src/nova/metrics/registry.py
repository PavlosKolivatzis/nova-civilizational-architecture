"""
Centralized Prometheus metrics registry to prevent duplicate registrations.

Phase 14-2: Merkle Checkpoints & PQC Signer
"""

from prometheus_client import REGISTRY, Counter, Gauge, Summary, ProcessCollector, PlatformCollector, GCCollector


_metric_cache = {}

# Initialize default collectors
_initialized = False

def init_default_collectors():
    """Initialize default Prometheus collectors if not already present."""
    global _initialized
    if _initialized:
        return

    # Check if process collector already registered
    collectors = list(REGISTRY._collector_to_names.keys()) if hasattr(REGISTRY, '_collector_to_names') else []
    has_process = any(isinstance(c, ProcessCollector) for c in collectors)
    has_platform = any(isinstance(c, PlatformCollector) for c in collectors)
    has_gc = any(isinstance(c, GCCollector) for c in collectors)

    if not has_process:
        ProcessCollector(registry=REGISTRY)
    if not has_platform:
        PlatformCollector(registry=REGISTRY)
    if not has_gc:
        GCCollector(registry=REGISTRY)

    _initialized = True

init_default_collectors()


def _get_existing(name: str):
    """Get existing collector from registry if it exists."""
    collectors = getattr(REGISTRY, "_names_to_collectors", {})
    return collectors.get(name)


def get_counter(name: str, desc: str, labelnames=()):
    """Get or create a Counter, reusing existing if already registered."""
    key = ("counter", name, tuple(labelnames))
    if key in _metric_cache:
        return _metric_cache[key]

    existing = _get_existing(name)
    if existing:
        _metric_cache[key] = existing
        return existing

    c = Counter(name, desc, labelnames=labelnames, registry=REGISTRY)
    _metric_cache[key] = c
    return c


def get_gauge(name: str, desc: str, labelnames=()):
    """Get or create a Gauge, reusing existing if already registered."""
    key = ("gauge", name, tuple(labelnames))
    if key in _metric_cache:
        return _metric_cache[key]

    existing = _get_existing(name)
    if existing:
        _metric_cache[key] = existing
        return existing

    g = Gauge(name, desc, labelnames=labelnames, registry=REGISTRY)
    _metric_cache[key] = g
    return g


def get_summary(name: str, desc: str, labelnames=()):
    """Get or create a Summary, reusing existing if already registered."""
    key = ("summary", name, tuple(labelnames))
    if key in _metric_cache:
        return _metric_cache[key]

    existing = _get_existing(name)
    if existing:
        _metric_cache[key] = existing
        return existing

    s = Summary(name, desc, labelnames=labelnames, registry=REGISTRY)
    _metric_cache[key] = s
    return s
