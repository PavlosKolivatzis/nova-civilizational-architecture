"""Public Prometheus registry for Nova."""

from prometheus_client import CollectorRegistry, GCCollector, ProcessCollector, PlatformCollector

nova_public_registry = CollectorRegistry()
GCCollector(registry=nova_public_registry)
ProcessCollector(registry=nova_public_registry)
PlatformCollector(registry=nova_public_registry)

__all__ = ["nova_public_registry"]
