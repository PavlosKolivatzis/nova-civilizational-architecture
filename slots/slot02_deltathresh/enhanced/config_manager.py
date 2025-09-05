"""Runtime configuration manager for ΔTHRESH Slot 2."""

from __future__ import annotations

import json
import logging
import threading
from pathlib import Path
from typing import Callable, List, Optional

import yaml

from .config import EnhancedProcessingConfig


class ConfigManager:
    """Utility that manages :class:`EnhancedProcessingConfig` instances.

    The manager provides simple runtime updates and the ability to load
    configuration data from JSON/YAML files.  If a configuration file is
    supplied, the :meth:`watch` method can be used to reload changes when
    the file on disk is modified.
    """

    def __init__(self, initial_config: Optional[EnhancedProcessingConfig] = None) -> None:
        self.config: EnhancedProcessingConfig = (
            initial_config or EnhancedProcessingConfig.from_environment()
        )

        is_valid, violations = self.config.validate_runtime()
        if not is_valid:
            raise ValueError(f"Initial config validation failed: {violations}")

        self._lock = threading.RLock()
        self._listeners: List[Callable[[EnhancedProcessingConfig], None]] = []
        self._config_file: Optional[Path] = None
        self._last_mtime: float = 0.0

    # ------------------------------------------------------------------
    # listener management
    # ------------------------------------------------------------------
    def add_listener(self, listener: Callable[[EnhancedProcessingConfig], None]) -> None:
        with self._lock:
            self._listeners.append(listener)

    def _notify(self) -> None:
        for listener in self._listeners:
            try:
                listener(self.config)
            except Exception as exc:  # pragma: no cover - listeners are external
                logging.error("Config listener failed: %s", exc)

    # ------------------------------------------------------------------
    # configuration loading & updating
    # ------------------------------------------------------------------
    def update_config(self, new_config: EnhancedProcessingConfig) -> bool:
        """Replace the current config after validation."""

        is_valid, violations = new_config.validate_runtime()
        if not is_valid:
            raise ValueError(f"Configuration validation failed: {violations}")

        with self._lock:
            self.config = new_config
            self._notify()
        return True

    def load_from_file(self, path: Path) -> bool:
        """Load configuration from a YAML or JSON file."""

        if not path.exists():
            raise FileNotFoundError(f"Configuration file not found: {path}")

        with path.open("r", encoding="utf-8") as fh:
            if path.suffix.lower() in {".yml", ".yaml"}:
                data = yaml.safe_load(fh)
            else:
                data = json.load(fh)

        cfg = EnhancedProcessingConfig.from_dict(data)
        updated = self.update_config(cfg)
        self._config_file = path
        self._last_mtime = path.stat().st_mtime
        return updated

    def watch(self) -> None:
        """Reload configuration if the watched file has changed."""

        if not self._config_file:
            return

        current_mtime = self._config_file.stat().st_mtime
        if current_mtime > self._last_mtime:
            self.load_from_file(self._config_file)

