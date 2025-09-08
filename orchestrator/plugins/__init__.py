"""Plugin system for NOVA slots.

The public API re-exports the common plugin types and utilities so that tests
and applications can import them from this package directly.
"""

from .abc import SlotPlugin
from .loader import PluginLoader
from .filepython import PythonFilePlugin
from .rest import RestAPIPlugin

__all__ = [
    "SlotPlugin",
    "PluginLoader",
    "PythonFilePlugin",
    "RestAPIPlugin",
]
