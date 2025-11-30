from __future__ import annotations

import importlib.util
import os
from pathlib import Path
from types import ModuleType
from typing import Any


class PythonFilePlugin:
    """Load and execute a function from a Python file.

    The default entry point is a function named ``run`` which can accept
    arbitrary positional and keyword arguments.  The plugin file is imported
    dynamically each time :meth:`run` is invoked to ensure the latest
    version is executed.

    Security (P1-HR1): Plugin paths are validated to prevent arbitrary code execution.
    Plugins must be within NOVA_PLUGIN_DIR and have .py extension.
    """

    def __init__(self, path: str, func_name: str = "run") -> None:
        self.path = Path(path).resolve()  # Resolve to absolute path
        self.func_name = func_name

        # P1-HR1: Validate plugin path (CVSS 7.5 - Code execution prevention)
        self._validate_plugin_path()

        if not self.path.exists():  # pragma: no cover - simple validation
            raise FileNotFoundError(path)

    def _validate_plugin_path(self) -> None:
        """Validate that plugin path is safe to load.

        Security checks:
        1. Path must be within NOVA_PLUGIN_DIR (default: ./plugins)
        2. File extension must be .py
        3. Path must not contain directory traversal attempts
        """
        # Get trusted plugin directory
        plugin_dir_str = os.getenv("NOVA_PLUGIN_DIR", "./plugins")
        plugin_dir = Path(plugin_dir_str).resolve()

        # Check 1: Must be within plugin directory
        try:
            self.path.relative_to(plugin_dir)
        except ValueError:
            raise ValueError(
                f"Security: Plugin path must be within {plugin_dir}. "
                f"Got: {self.path}. Set NOVA_PLUGIN_DIR to change plugin directory."
            )

        # Check 2: Must be a .py file
        if self.path.suffix != ".py":
            raise ValueError(
                f"Security: Plugin must be a .py file. Got: {self.path.suffix}"
            )

    def _load_module(self) -> ModuleType:
        spec = importlib.util.spec_from_file_location(self.path.stem, self.path)
        if spec is None or spec.loader is None:  # pragma: no cover - safety
            raise ImportError(f"Cannot load module from {self.path}")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    def run(self, *args: Any, **kwargs: Any) -> Any:
        module = self._load_module()
        func = getattr(module, self.func_name, None)
        if not callable(func):  # pragma: no cover - defensive
            raise AttributeError(
                f"Function '{self.func_name}' not found in plugin {self.path}"
            )
        return func(*args, **kwargs)
