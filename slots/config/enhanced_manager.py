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
    # Optional dependency: watchdog (preferred hot-reload backend)
    from watchdog.observers import Observer
    from watchdog.events import FileSystemEventHandler
    _WATCHDOG_AVAILABLE = True
except Exception:  # ImportError or any env-specific failure
    Observer = None  # type: ignore
    FileSystemEventHandler = object  # type: ignore
    _WATCHDOG_AVAILABLE = False
    # We intentionally do NOT hard-fail here. Hot-reload will fall back to polling.
    # To enable watchdog-based reloads:
    #   pip install watchdog
    # or enable the 'hotreload' extra if using pyproject (see patch below).

# Back-compat alias for tests that patch `_WATCHDOG`
_WATCHDOG = _WATCHDOG_AVAILABLE


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

        # Serverless detection (Vercel/Lambda/GCF) → force-disable hot reload
        serverless = bool(
            os.getenv("VERCEL") or
            os.getenv("VERCEL_ENV") or
            os.getenv("AWS_LAMBDA_FUNCTION_NAME") or
            os.getenv("FUNCTION_TARGET") or
            os.getenv("K_SERVICE")
        )
        env_toggle = os.getenv("NOVA_HOT_RELOAD")  # explicit override
        self.enable_hot_reload = (
            False if serverless else enable_hot_reload
        ) if env_toggle is None else (env_toggle.lower() == "true")
        if serverless and self.enable_hot_reload:
            # explicit override was TRUE in serverless; flip off and log
            self.enable_hot_reload = False
        if serverless:
            logger.info("Serverless environment detected → hot reload disabled")

        self._observer: Optional[Observer] = None  # type: ignore
        self._lock = threading.RLock()
        self._loop: Optional[asyncio.AbstractEventLoop] = None
        self._last_event: Dict[str, float] = {}
        self._debounce_ms: int = 250
        self._poll_task: Optional[asyncio.Task] = None

        # --- Back-compat shim so old tests that expect a thread-based poller still pass ---
        class _AsyncTaskThreadShim:
            def __init__(self, task_getter: Callable[[], Optional[asyncio.Task]]):
                self._task_getter = task_getter
            def is_alive(self) -> bool:
                t = self._task_getter()
                return bool(t and not t.done())
        self._poll_thread = _AsyncTaskThreadShim(lambda: self._poll_task)
        # -----------------------------------------------------------------------------------

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
        # Capture the owning event loop so background threads can marshal work back safely
        self._loop = asyncio.get_running_loop()
        await self._load_all_metadata()

        if self.enable_hot_reload:
            if _WATCHDOG_AVAILABLE and _WATCHDOG:
                self._setup_config_watcher()
            else:
                self._setup_polling_watcher()

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

    def _setup_config_watcher(self) -> None:
        """Setup file system watcher for hot-reload"""
        if not _WATCHDOG_AVAILABLE or not _WATCHDOG:
            logger.info("Watchdog not available; skipping file-system watcher.")
            return

        class ConfigChangeHandler(FileSystemEventHandler):  # type: ignore[misc]
            def __init__(self, manager):
                self.manager = manager

            def on_modified(self, event):
                if not event.is_directory and event.src_path.endswith((".yaml", ".yml")):
                    # Debounce frequent editor events
                    now = datetime.now().timestamp() * 1000
                    last = self.manager._last_event.get(event.src_path, 0)
                    if (now - last) < self.manager._debounce_ms:
                        return
                    self.manager._last_event[event.src_path] = now

                    # We are in a watchdog thread; marshal onto the manager's loop safely
                    if self.manager._loop is not None:
                        asyncio.run_coroutine_threadsafe(
                            self.manager._handle_config_change(event.src_path),
                            self.manager._loop,
                        )

        self._observer = Observer()
        self._observer.schedule(
            ConfigChangeHandler(self),
            str(self.config_dir),
            recursive=True,
        )
        self._observer.start()
        logger.info("Configuration hot-reload enabled")

    def _setup_polling_watcher(self) -> None:
        """Lightweight polling fallback if watchdog isn't installed."""
        async def poll_loop():
            logger.info("Configuration hot-reload (polling) enabled")
            # naive mtime cache
            mtimes: Dict[Path, float] = {}
            while True:
                try:
                    for yaml_path in self.config_dir.rglob("*.yml"):
                        await self._maybe_reload_path(yaml_path, mtimes)
                    for yaml_path in self.config_dir.rglob("*.yaml"):
                        await self._maybe_reload_path(yaml_path, mtimes)
                    await asyncio.sleep(1.0)  # 1s poll interval
                except asyncio.CancelledError:
                    break
                except Exception as e:
                    logger.error(f"Polling watcher error: {e}")

        if self._loop:
            self._poll_task = self._loop.create_task(poll_loop())

    async def _maybe_reload_path(self, yaml_path: Path, mtimes: Dict[Path, float]) -> None:
        try:
            mtime = yaml_path.stat().st_mtime
        except FileNotFoundError:
            return
        last = mtimes.get(yaml_path)
        if last is None:
            mtimes[yaml_path] = mtime
            return
        if mtime > last:
            # Debounce per path
            now = datetime.now().timestamp() * 1000
            last_evt = self._last_event.get(str(yaml_path), 0)
            if (now - last_evt) < self._debounce_ms:
                return
            self._last_event[str(yaml_path)] = now
            mtimes[yaml_path] = mtime
            await self._handle_config_change(str(yaml_path))

    async def _handle_config_change(self, config_path: str) -> None:
        try:
            with self._lock:
                path = Path(config_path)
                slot_id = self._extract_slot_id(path.parent.name)

                if slot_id in self.slot_metadata:
                    # Stage new values; only swap on success
                    staged_metadata = SlotMetadata.from_yaml(config_path)
                    staged_config = self._build_runtime_config(slot_id, staged_metadata)
                    if not staged_metadata.validate_schema(staged_config):
                        logger.error(f"Schema validation failed for Slot {slot_id}; keeping previous config")
                        return

                    old_config = self.runtime_configs.get(slot_id, {}).copy()
                    self.slot_metadata[slot_id] = staged_metadata
                    self.runtime_configs[slot_id] = staged_config
                else:
                    return

            # Notify outside the lock
            await self._notify_config_change(slot_id, old_config, self.runtime_configs[slot_id])
            logger.info(f"Hot-reloaded configuration for Slot {slot_id}")

        except Exception as e:
            logger.error(f"Failed to handle config change for {config_path}: {e}")

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
        """Shutdown configuration manager"""
        if self._poll_task:
            self._poll_task.cancel()
            try:
                await self._poll_task
            except asyncio.CancelledError:
                pass
        if self._observer:
            self._observer.stop()
            self._observer.join()
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
