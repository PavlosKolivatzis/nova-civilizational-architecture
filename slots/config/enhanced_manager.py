"""Enhanced Configuration Manager - Nova-compatible, production-safe."""

from __future__ import annotations

import os
import yaml
import asyncio
import logging
from pathlib import Path
from dataclasses import dataclass, field, asdict
from typing import Dict, Any, Optional, List, Callable
import threading
from datetime import datetime

logger = logging.getLogger("nova.config")

# --- Optional watchdog (fallback to polling if unavailable) -------------------
try:
    from watchdog.observers import Observer  # type: ignore
    from watchdog.events import FileSystemEventHandler  # type: ignore
    _WATCHDOG = True
except Exception:  # pragma: no cover
    _WATCHDOG = False
    Observer = None  # type: ignore
    FileSystemEventHandler = object  # type: ignore


# --- Data ---------------------------------------------------------------------

@dataclass
class SlotMetadata:
    """Enhanced slot metadata - extends existing slotX.meta.yaml pattern."""
    slot: int
    name: str
    version: str
    entry_point: str
    adapter: Optional[str] = None
    description: Optional[str] = None
    inputs: Optional[Dict[str, str]] = None
    outputs: Optional[Dict[str, str]] = None
    metrics: Optional[List[str]] = None
    ci: Optional[Dict[str, Any]] = None

    # Enhanced capabilities
    config_schema: Optional[Dict[str, Any]] = None
    runtime_constraints: Optional[Dict[str, Any]] = None
    dependencies: List[str] = field(default_factory=list)
    security_level: str = "standard"
    performance_targets: Optional[Dict[str, float]] = None

    @classmethod
    def from_yaml(cls, yaml_path: str) -> "SlotMetadata":
        """Load metadata (local discovery; no hard dependency on slot_loader)."""
        path = Path(yaml_path)
        if not path.exists():
            matches = list(Path.cwd().glob(yaml_path)) or list(Path.cwd().glob(f"**/{yaml_path}"))
            if not matches:
                raise FileNotFoundError(f"Metadata not found: {yaml_path}")
            path = matches[0]
        with path.open("r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
        return cls(**data)

    def validate_schema(self, config_data: Dict[str, Any]) -> bool:
        """Very light schema check; upgrade to jsonschema if needed."""
        if not self.config_schema:
            return True
        type_map = {"float": (int, float), "int": int, "str": str, "bool": bool}
        for key, typ in self.config_schema.items():
            if key in config_data:
                ok_types = type_map.get(typ, object)
                if not isinstance(config_data[key], ok_types):
                    return False
        return True


# --- Manager ------------------------------------------------------------------

class EnhancedConfigManager:
    """
    Enhanced configuration system that preserves Nova env precedence
    and adds hot-reload, validation, and hierarchical overrides.
    """

    def __init__(self, config_dir: str = "slots", enable_hot_reload: bool = True):
        self.config_dir = Path(config_dir)
        self.slot_metadata: Dict[int, SlotMetadata] = {}
        self.runtime_configs: Dict[int, Dict[str, Any]] = {}
        self._listeners: List[Callable[[int, Dict[str, Any], Dict[str, Any]], None]] = []
        self.enable_hot_reload = enable_hot_reload
        self._observer: Optional[Observer] = None  # type: ignore
        self._lock = threading.RLock()
        self._loop: Optional[asyncio.AbstractEventLoop] = None
        self._poll_thread: Optional[threading.Thread] = None
        self._mtimes: Dict[Path, float] = {}

        # Preserve optional SystemConfig
        try:
            from orchestrator.config import config as system_config  # type: ignore
            self.system_config = system_config
            logger.info("Loaded existing Nova SystemConfig")
        except Exception:
            self.system_config = None
            logger.info("Nova SystemConfig not found – proceeding with defaults")

    async def initialize(self) -> None:
        """Initialize manager (discover slots, load configs, start watching)."""
        logger.info("Initializing Enhanced Configuration Manager")
        self._loop = asyncio.get_running_loop()
        await self._load_all_metadata()
        if self.enable_hot_reload:
            if _WATCHDOG:
                self._setup_watchdog(self._loop)
            else:
                self._start_polling_watcher()  # fallback
        logger.info("Configuration manager ready: %d slots", len(self.slot_metadata))

    async def _load_all_metadata(self) -> None:
        for slot_dir in sorted(self.config_dir.glob("slot*")):
            if not slot_dir.is_dir():
                continue
            slot_id = self._extract_slot_id(slot_dir.name)
            for meta_path in (
                slot_dir / f"{slot_dir.name}.meta.yaml",
                slot_dir / "meta.yaml",
                slot_dir / "slot.yaml",
            ):
                if meta_path.exists():
                    try:
                        metadata = SlotMetadata.from_yaml(str(meta_path))
                        with self._lock:
                            self.slot_metadata[slot_id] = metadata
                            self.runtime_configs[slot_id] = self._build_runtime_config(slot_id, metadata)
                            self._mtimes[meta_path] = meta_path.stat().st_mtime
                        logger.debug("Loaded configuration for Slot %d from %s", slot_id, meta_path)
                    except Exception as e:
                        logger.error("Failed to load %s: %s", meta_path, e)
                    break

    @staticmethod
    def _extract_slot_id(dir_name: str) -> int:
        digits = "".join(ch for ch in dir_name if ch.isdigit())
        return int(digits) if digits else 0

    def _build_runtime_config(self, slot_id: int, metadata: SlotMetadata) -> Dict[str, Any]:
        cfg: Dict[str, Any] = {}
        cfg.update(asdict(metadata))  # base metadata

        # Env overrides (Nova precedence preserved)
        cfg.update(self._extract_env_overrides(slot_id))

        # SystemConfig overrides (if available)
        if self.system_config:
            cfg.update(self._extract_system_config_overrides(slot_id))

        # Validate
        if not metadata.validate_schema(cfg):
            logger.warning("Configuration validation failed for Slot %d", slot_id)

        return cfg

    @staticmethod
    def _parse_env_value(value: str) -> Any:
        v = value.strip()
        low = v.lower()
        if low in ("true", "false"):
            return low == "true"
        try:
            if "." in v:
                return float(v)
            return int(v)
        except ValueError:
            return v

    def _extract_env_overrides(self, slot_id: int) -> Dict[str, Any]:
        overrides: Dict[str, Any] = {}
        prefixes = (f"NOVA_SLOT{slot_id:02d}_", f"NOVA_SLOT{slot_id}_", f"SLOT{slot_id}_")
        for key, value in os.environ.items():
            for p in prefixes:
                if key.startswith(p):
                    config_key = key[len(p):].lower()
                    overrides[config_key] = self._parse_env_value(value)
                    break
        return overrides

    def _extract_system_config_overrides(self, slot_id: int) -> Dict[str, Any]:
        sc = self.system_config
        if not sc:
            return {}
        out: Dict[str, Any] = {}
        if slot_id == 4 and hasattr(sc, "TRUTH_THRESHOLD"):
            out["truth_threshold"] = sc.TRUTH_THRESHOLD
        if slot_id == 6 and hasattr(sc, "CULTURAL_WEIGHTS"):
            out["cultural_weights"] = sc.CULTURAL_WEIGHTS
        if slot_id == 9 and hasattr(sc, "DISTORTION_DETECTION_SENSITIVITY"):
            out["detection_sensitivity"] = sc.DISTORTION_DETECTION_SENSITIVITY
        return out

    # --- Watching -------------------------------------------------------------

    def _setup_watchdog(self, loop: asyncio.AbstractEventLoop) -> None:
        assert _WATCHDOG and Observer is not None and FileSystemEventHandler is not object

        class ConfigChangeHandler(FileSystemEventHandler):  # type: ignore
            def __init__(self, manager: "EnhancedConfigManager", loop_: asyncio.AbstractEventLoop):
                self.manager = manager
                self.loop = loop_

            def on_modified(self, event):  # runs in watchdog thread
                if getattr(event, "is_directory", False):
                    return
                path = str(getattr(event, "src_path", ""))
                if path.endswith((".yaml", ".yml")):
                    fut = asyncio.run_coroutine_threadsafe(
                        self.manager._handle_config_change(path), self.loop
                    )
                    # best-effort: log exceptions from the scheduled task
                    try:
                        fut.result(timeout=0)  # non-blocking check
                    except Exception:  # pragma: no cover
                        pass

        self._observer = Observer()  # type: ignore
        self._observer.schedule(ConfigChangeHandler(self, loop), str(self.config_dir), recursive=True)
        self._observer.start()
        logger.info("Configuration hot-reload enabled (watchdog)")

    def _start_polling_watcher(self, interval: float = 1.0) -> None:
        """Fallback watcher using mtimes (no external deps)."""
        def _poll():
            while True:
                try:
                    with self._lock:
                        meta_files = []
                        for slot_dir in self.config_dir.glob("slot*"):
                            for meta in (
                                slot_dir / f"{slot_dir.name}.meta.yaml",
                                slot_dir / "meta.yaml",
                                slot_dir / "slot.yaml",
                            ):
                                if meta.exists():
                                    meta_files.append(meta)
                    for meta in meta_files:
                        try:
                            m = meta.stat().st_mtime
                        except FileNotFoundError:
                            continue
                        last = self._mtimes.get(meta, 0.0)
                        if m > last:
                            self._mtimes[meta] = m
                            # schedule async handler on loop
                            if self._loop:
                                asyncio.run_coroutine_threadsafe(
                                    self._handle_config_change(str(meta)), self._loop
                                )
                    # sleep
                    if interval <= 0:
                        break
                    threading.Event().wait(interval)
                except Exception as e:  # pragma: no cover
                    logger.error("Polling watcher error: %s", e)
                    threading.Event().wait(interval)

        self._poll_thread = threading.Thread(target=_poll, name="nova-config-poller", daemon=True)
        self._poll_thread.start()
        logger.info("Configuration hot-reload enabled (polling)")

    async def _handle_config_change(self, config_path: str) -> None:
        try:
            path = Path(config_path)
            slot_id = self._extract_slot_id(path.parent.name)
            if slot_id not in self.slot_metadata:
                return
            new_meta = SlotMetadata.from_yaml(str(path))
            new_cfg = self._build_runtime_config(slot_id, new_meta)
            with self._lock:
                old_cfg = dict(self.runtime_configs.get(slot_id, {}))
                self.slot_metadata[slot_id] = new_meta
                self.runtime_configs[slot_id] = new_cfg
                self._mtimes[path] = path.stat().st_mtime
            await self._notify_config_change(slot_id, old_cfg, new_cfg)
            logger.info("Hot-reloaded configuration for Slot %d", slot_id)
        except Exception as e:
            logger.error("Failed to handle config change for %s: %s", config_path, e)

    async def _notify_config_change(self, slot_id: int, old_config: Dict[str, Any], new_config: Dict[str, Any]) -> None:
        # Copy listeners to avoid mutation during iteration
        with self._lock:
            listeners = list(self._listeners)
        for listener in listeners:
            try:
                if asyncio.iscoroutinefunction(listener):
                    await listener(slot_id, old_config, new_config)
                else:
                    listener(slot_id, old_config, new_config)
            except Exception as e:
                logger.error("Config change listener failed: %s", e)

    # --- Public API -----------------------------------------------------------

    def register_config_listener(self, listener: Callable[[int, Dict[str, Any], Dict[str, Any]], None]) -> None:
        with self._lock:
            self._listeners.append(listener)

    def get_slot_config(self, slot_id: int, overrides: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        with self._lock:
            base = dict(self.runtime_configs.get(slot_id, {}))
        if overrides:
            base.update(overrides)
        return base

    def get_slot_metadata(self, slot_id: int) -> Optional[SlotMetadata]:
        with self._lock:
            return self.slot_metadata.get(slot_id)

    def list_slots(self) -> List[int]:
        with self._lock:
            return list(self.slot_metadata.keys())

    def export_config(self, slot_id: int) -> Dict[str, Any]:
        with self._lock:
            metadata = self.slot_metadata.get(slot_id)
            runtime_config = dict(self.runtime_configs.get(slot_id, {}))
        return {
            "slot_id": slot_id,
            "metadata": asdict(metadata) if metadata else None,
            "runtime_config": runtime_config,
            "timestamp": datetime.now().isoformat(),
        }

    async def shutdown(self) -> None:
        if self._observer:
            self._observer.stop()
            self._observer.join()
        if self._poll_thread and self._poll_thread.is_alive():
            # let it die naturally; it's daemonized
            pass
        logger.info("Configuration manager shutdown complete")


# --- Global instance + convenience -------------------------------------------

_global_config_manager: Optional[EnhancedConfigManager] = None
_global_lock = threading.Lock()

async def get_config_manager() -> EnhancedConfigManager:
    global _global_config_manager
    if _global_config_manager is None:
        with _global_lock:
            if _global_config_manager is None:
                mgr = EnhancedConfigManager()
                await mgr.initialize()
                _global_config_manager = mgr
    return _global_config_manager

def get_slot_config(slot_id: int, **overrides) -> Dict[str, Any]:
    """Sync wrapper that works in both async and sync contexts."""
    try:
        loop = asyncio.get_running_loop()
        # already in async context
        mgr = _global_config_manager
        if mgr is None:
            # lazily init without blocking the running loop
            # caller should prefer the async API for first use
            return {}
        return mgr.get_slot_config(slot_id, overrides)
    except RuntimeError:
        # no running loop → safe synchronous call
        async def _inner():
            mgr = await get_config_manager()
            return mgr.get_slot_config(slot_id, overrides)
        return asyncio.run(_inner())


if __name__ == "__main__":  # manual test
    async def main():
        mgr = await get_config_manager()
        slot6 = mgr.get_slot_config(6)
        print("Slot 6 Configuration:", slot6)

        def on_change(slot_id, old_cfg, new_cfg):
            print(f"[change] slot {slot_id}: keys {set(old_cfg)!=set(new_cfg)}")

        mgr.register_config_listener(on_change)

        debug = mgr.export_config(6)
        print("Debug Info:", debug)

    asyncio.run(main())
