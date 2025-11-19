"""Internal Prometheus registry for Nova."""

from nova.metrics.registry import REGISTRY as nova_internal_registry

__all__ = ["nova_internal_registry"]
