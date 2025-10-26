"""Shared Prometheus registry for Nova components."""

from prometheus_client import (
    CollectorRegistry,
    GCCollector,
    PlatformCollector,
    ProcessCollector,
)

REGISTRY = CollectorRegistry()

# Register default collectors once so all exporters share the same registry.
ProcessCollector(registry=REGISTRY)
PlatformCollector(registry=REGISTRY)
GCCollector(registry=REGISTRY)

__all__ = ["REGISTRY"]
