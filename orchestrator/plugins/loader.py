"""Plugin loader for NOVA slot system."""

from __future__ import annotations

import importlib
import pathlib
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Set

import yaml

from src_bootstrap import ensure_src_on_path
from .abc import SlotPlugin


@dataclass
class LoadedSlot:
    """Container for loaded slot metadata and plugin instance."""

    meta: Dict[str, Any]
    plugin: Optional[SlotPlugin]
    adapters: Dict[str, Any]


class PluginLoader:
    """Discovers and loads NOVA slot plugins based on configuration."""

    def __init__(
        self,
        slots_dirs: tuple[str, ...] = ("src/nova/slots", "slots"),
        enabled: Optional[List[str]] = None,
    ) -> None:
        ensure_src_on_path()
        self._roots = [pathlib.Path(d) for d in slots_dirs]
        self._enabled: Optional[Set[str]] = set(enabled) if enabled else None
        self._loaded: Dict[str, LoadedSlot] = {}

    def discover(self) -> Dict[str, LoadedSlot]:
        """Discover and load all slot plugins."""

        visited: Set[str] = set()
        for pkg in self._iter_slot_packages():
            slot_id = pkg.name
            if slot_id in visited:
                continue

            meta_path = pkg / f"{slot_id}.meta.yaml"
            if not meta_path.exists():
                continue

            try:
                meta = yaml.safe_load(meta_path.read_text()) or {}
            except Exception as exc:
                print(f" Failed to read metadata for {slot_id}: {exc}")
                continue

            visited.add(slot_id)

            if self._enabled and slot_id not in self._enabled:
                self._loaded[slot_id] = LoadedSlot(meta, None, {})
                continue

            module_candidates = (
                f"nova.slots.{slot_id}.plugin",
                f"slots.{slot_id}.plugin",
            )

            module = None
            for module_path in module_candidates:
                try:
                    module = importlib.import_module(module_path)
                    break
                except Exception:
                    module = None
            if not module:
                self._loaded[slot_id] = LoadedSlot(meta, None, {})
                continue

            plugin_class = None
            for name in dir(module):
                if name.endswith("Plugin") and not name.startswith("_"):
                    plugin_class = getattr(module, name)
                    break

            if plugin_class:
                try:
                    plugin: SlotPlugin = plugin_class()
                    adapters = plugin.adapters()
                except Exception as exc:
                    print(f" Failed to instantiate plugin {slot_id}: {exc}")
                    plugin = None
                    adapters = {}
                self._loaded[slot_id] = LoadedSlot(meta, plugin, adapters)
            else:
                self._loaded[slot_id] = LoadedSlot(meta, None, {})

        return self._loaded

    def _iter_slot_packages(self):
        for root in self._roots:
            if not root.exists():
                continue
            yield from sorted(p for p in root.glob("slot*/") if p.is_dir())

    def start_all(self, bus: Any, config: Dict[str, Any]) -> None:
        """Start all loaded plugins."""
        for slot_id, slot in self._loaded.items():
            if not slot.plugin:
                continue
            try:
                slot.plugin.start(bus, config.get(slot_id, {}))
                print(f" Started plugin: {slot_id}")
            except Exception as exc:
                print(f" Failed to start plugin {slot_id}: {exc}")

    def stop_all(self) -> None:
        """Stop all loaded plugins."""
        for slot_id, slot in self._loaded.items():
            if not slot.plugin:
                continue
            try:
                slot.plugin.stop()
                print(f" Stopped plugin: {slot_id}")
            except Exception as exc:
                print(f" Failed to stop plugin {slot_id}: {exc}")

    def providers_for(self, contract_id: str) -> Dict[str, Any]:
        """Get all providers for a specific contract ID."""
        return {
            slot_id: slot.adapters[contract_id]
            for slot_id, slot in self._loaded.items()
            if contract_id in slot.adapters
        }

    def items(self) -> Dict[str, LoadedSlot]:
        """Get all loaded slots."""
        return self._loaded

    def get_health(self) -> Dict[str, Any]:
        """Get health status of all plugins."""
        health: Dict[str, Any] = {}
        for slot_id, slot in self._loaded.items():
            if not slot.plugin:
                health[slot_id] = {"status": "not_loaded"}
                continue
            try:
                health[slot_id] = slot.plugin.health()
            except Exception as exc:
                health[slot_id] = {"error": str(exc)}
        return health
