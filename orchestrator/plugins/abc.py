"""Abstract base classes for NOVA slot plugin system."""

from __future__ import annotations
from typing import Protocol, Mapping, Callable, Any


class SlotPlugin(Protocol):
    """Protocol for NOVA slot plugins."""
    
    id: str           # e.g. "slot06_cultural_synthesis"
    version: str
    optional: bool
    
    def start(self, bus: Any, config: Mapping[str, Any]) -> None:
        """Initialize plugin with event bus and configuration."""
        ...
    
    def stop(self) -> None:
        """Cleanup plugin resources."""
        ...
    
    def health(self) -> Mapping[str, Any]:
        """Return plugin health status."""
        ...
    
    def adapters(self) -> Mapping[str, Callable[[Any], Any]]:
        """Return contract ID -> adapter function mappings."""
        ...