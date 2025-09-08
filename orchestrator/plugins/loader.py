"""Plugin loader for NOVA slot system."""

from __future__ import annotations
import importlib
import pathlib
import yaml
from dataclasses import dataclass
from typing import Dict, Any, Optional, Set, List

from .abc import SlotPlugin


@dataclass
class LoadedSlot:
    """Container for loaded slot metadata and plugin instance."""
    meta: Dict[str, Any]
    plugin: Optional[SlotPlugin]
    adapters: Dict[str, Any]


class PluginLoader:
    """Discovers and loads NOVA slot plugins based on configuration."""
    
    def __init__(self, slots_dir: str = "slots", enabled: Optional[List[str]] = None):
        self._root = pathlib.Path(slots_dir)
        self._enabled: Optional[Set[str]] = set(enabled) if enabled else None
        self._loaded: Dict[str, LoadedSlot] = {}
    
    def discover(self) -> Dict[str, LoadedSlot]:
        """Discover and load all slot plugins."""
        for pkg in sorted(self._root.glob("slot*/")):
            meta_path = pkg / f"{pkg.name}.meta.yaml"
            if not meta_path.exists():
                continue
                
            try:
                meta = yaml.safe_load(meta_path.read_text())
            except Exception:
                continue
                
            slot_id = meta.get("id", pkg.name)
            
            # Check if slot is enabled
            if self._enabled and slot_id not in self._enabled:
                self._loaded[slot_id] = LoadedSlot(meta, None, {})
                continue
            
            # Try to load the plugin
            try:
                module_path = f"{pkg.as_posix().replace('/', '.')}.plugin"
                mod = importlib.import_module(module_path)
                
                # Find plugin class (ends with "Plugin")
                plugin_class = None
                for name in dir(mod):
                    if name.endswith("Plugin") and not name.startswith("_"):
                        plugin_class = getattr(mod, name)
                        break
                
                if plugin_class:
                    plugin: SlotPlugin = plugin_class()
                    self._loaded[slot_id] = LoadedSlot(meta, plugin, plugin.adapters())
                else:
                    self._loaded[slot_id] = LoadedSlot(meta, None, {})
                    
            except Exception as e:
                print(f"⚠️ Failed to load plugin {slot_id}: {e}")
                self._loaded[slot_id] = LoadedSlot(meta, None, {})
                
        return self._loaded
    
    def start_all(self, bus: Any, config: Dict[str, Any]) -> None:
        """Start all loaded plugins."""
        for slot_id, slot in self._loaded.items():
            if slot.plugin:
                try:
                    slot.plugin.start(bus, config.get(slot_id, {}))
                    print(f"✅ Started plugin: {slot_id}")
                except Exception as e:
                    print(f"⚠️ Failed to start plugin {slot_id}: {e}")
    
    def stop_all(self) -> None:
        """Stop all loaded plugins."""
        for slot_id, slot in self._loaded.items():
            if slot.plugin:
                try:
                    slot.plugin.stop()
                    print(f"✅ Stopped plugin: {slot_id}")
                except Exception as e:
                    print(f"⚠️ Failed to stop plugin {slot_id}: {e}")
    
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
        health = {}
        for slot_id, slot in self._loaded.items():
            if slot.plugin:
                try:
                    health[slot_id] = slot.plugin.health()
                except Exception as e:
                    health[slot_id] = {"error": str(e)}
            else:
                health[slot_id] = {"status": "not_loaded"}
        return health