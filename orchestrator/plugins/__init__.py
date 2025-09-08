"""Plugin system for NOVA slots."""

from .abc import SlotPlugin
from .loader import PluginLoader

__all__ = ["SlotPlugin", "PluginLoader"]
