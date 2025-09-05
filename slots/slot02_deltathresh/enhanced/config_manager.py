from __future__ import annotations

from pathlib import Path
from typing import Callable, List, Optional
import threading
import yaml

from .config import EnhancedProcessingConfig, OperationalMode  # noqa: F401  (used in tests)


class ConfigManager:
    def __init__(self, initial_config: Optional[EnhancedProcessingConfig] = None) -> None:
        # Build config (env-backed if none provided)
        self.config: EnhancedProcessingConfig = (
            initial_config or EnhancedProcessingConfig.from_environment()
        )

        # Lightweight runtime validation
        is_valid, violations = self.config.validate_runtime()
        if not is_valid:
            raise ValueError(f"Initial config validation failed: {violations}")

        # State for hot-reload & observers
        self._lock = threading.RLock()
        self._listeners: List[Callable[[EnhancedProcessingConfig], None]] = []
        self._config_file: Optional[Path] = None
        self._last_mtime: float = 0.0

    def add_listener(self, cb: Callable[[EnhancedProcessingConfig], None]) -> None:
        with self._lock:
            self._listeners.append(cb)

    def _notify(self) -> None:
        for cb in list(self._listeners):
            try:
                cb(self.config)
            except Exception:
                # listeners are best-effort; don't crash the manager
                pass

    def load_from_file(self, path: Path) -> None:
        """Replace current config from YAML file and validate."""
        with self._lock:
            data = yaml.safe_load(path.read_text()) or {}
            new_cfg = EnhancedProcessingConfig.from_dict(data)

            is_valid, violations = new_cfg.validate_runtime()
            if not is_valid:
                raise ValueError(f"Loaded config validation failed: {violations}")

            self.config = new_cfg
            self._config_file = path
            self._last_mtime = path.stat().st_mtime

        self._notify()

    def maybe_reload(self) -> bool:
        """Reload if the bound file changed. Returns True if reloaded."""
        if not self._config_file:
            return False
        try:
            mtime = self._config_file.stat().st_mtime
        except FileNotFoundError:
            return False
        if mtime <= self._last_mtime:
            return False
        self.load_from_file(self._config_file)
        return True

