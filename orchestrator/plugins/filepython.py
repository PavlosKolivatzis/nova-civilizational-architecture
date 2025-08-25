from __future__ import annotations

import importlib.util
from pathlib import Path
from types import ModuleType
from typing import Any


class PythonFilePlugin:
    """Load and execute a function from a Python file.

    The default entry point is a function named ``run`` which can accept
    arbitrary positional and keyword arguments.  The plugin file is imported
    dynamically each time :meth:`run` is invoked to ensure the latest
    version is executed.
    """

    def __init__(self, path: str, func_name: str = "run") -> None:
        self.path = Path(path)
        self.func_name = func_name
        if not self.path.exists():  # pragma: no cover - simple validation
            raise FileNotFoundError(path)

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
