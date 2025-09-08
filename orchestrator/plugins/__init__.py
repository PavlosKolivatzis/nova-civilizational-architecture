"""Plugin system for NOVA slots."""

from .filepython import PythonFilePlugin
from .rest import RestAPIPlugin

__all__ = ["PythonFilePlugin", "RestAPIPlugin"]
