"""Enhanced Configuration Manager - Building on Nova's meta.yaml innovation
Preserves ALL existing patterns while adding enterprise capabilities
"""

import os
import yaml
import asyncio
import logging
from pathlib import Path
from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List, Callable
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import threading
from datetime import datetime

logger = logging.getLogger("nova.config")

@dataclass
class SlotMetadata:
    """Enhanced slot metadata - EXTENDS your existing slot6.meta.yaml pattern"""
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
    
    # NEW: Enhanced capabilities
    config_schema: Optional[Dict[str, Any]] = None
    runtime_constraints: Optional[Dict[str, Any]] = None
    dependencies: List[str] = field(default_factory=list)
    security_level: str = "standard"
    performance_targets: Optional[Dict[str, float]] = None
    
    @classmethod
    def from_yaml(cls, yaml_path: str) -> 'SlotMetadata':
        """Load metadata using YOUR existing pattern with enhancements"""
        path = Path(yaml_path)
        if not path.exists():
            # Fallback to Nova's fuzzy file discovery
            from slot_loader import find_file
            path = Path(find_file(yaml_path))
        
        with open(path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
            return cls(**data)
    
    def validate_schema(self, config_data: Dict[str, Any]) -> bool:
        """Validate configuration against schema"""
        if not self.config_schema:
            return True
        
        # Basic validation - can be enhanced with jsonschema
        for key, expected_type in self.config_schema.items():
            if key in config_data:
                value = config_data[key]
                if expected_type == "float" and not isinstance(value, (int, float)):
                    return False
                elif expected_type == "int" and not isinstance(value, int):
                    return False
                elif expected_type == "str" and not isinstance(value, str):
                    return False
        return True

class EnhancedConfigManager:
    """
    Enhanced configuration system that PRESERVES Nova's environment variable precedence
    Adds hot-reload, validation, and hierarchical configuration capabilities
    """
    
    def __init__(self, config_dir: str = "slots", enable_hot_reload: bool = True):
        self.config_dir = Path(config_dir)
        self.slot_metadata: Dict[int, SlotMetadata] = {}
        self.runtime_configs: Dict[int, Dict[str, Any]] = {}
        self.config_listeners: List[Callable] = []
        self.enable_hot_reload = enable_hot_reload
        self._observer: Optional[Observer] = None
        self._lock = threading.RLock()
        
        # PRESERVE Nova's existing SystemConfig
        try:
            from orchestrator.config import config as system_config
            self.system_config = system_config
            logger.info("Loaded existing Nova SystemConfig")
        except ImportError:
            logger.warning("Nova SystemConfig not found - using defaults")
            self.system_config = None
    
    async def initialize(self) -> None:
        """Initialize configuration system"""
        logger.info("Initializing Enhanced Configuration Manager")
        await self._load_all_metadata()
        
        if self.enable_hot_reload:
            self._setup_config_watcher()
        
        logger.info(f"Configuration manager initialized with {len(self.slot_metadata)} slots")
    
    async def _load_all_metadata(self) -> None:
        """Load all slot metadata using Nova's discovery pattern"""
        for slot_dir in self.config_dir.glob("slot*"):
            if slot_dir.is_dir():
                # Check for existing meta.yaml pattern
                meta_patterns = [
                    slot_dir / f"{slot_dir.name}.meta.yaml",
                    slot_dir / "meta.yaml",
                    slot_dir / "slot.yaml"
                ]
                
                for meta_path in meta_patterns:
                    if meta_path.exists():
                        try:
                            slot_id = self._extract_slot_id(slot_dir.name)
                            metadata = SlotMetadata.from_yaml(str(meta_path))
                            self.slot_metadata[slot_id] = metadata
                            
                            # Load runtime configuration
                            runtime_config = self._build_runtime_config(slot_id, metadata)
                            self.runtime_configs[slot_id] = runtime_config
                            
                            logger.debug(f"Loaded configuration for Slot {slot_id}")
                            break
                        except Exception as e:
                            logger.error(f"Failed to load metadata from {meta_path}: {e}")
    
    def _extract_slot_id(self, dir_name: str) -> int:
        """Extract slot ID from directory name"""
        # Handle slot02_deltathresh, slot06_cultural_synthesis, etc.
        numbers = ''.join(filter(str.isdigit, dir_name))
        return int(numbers) if numbers else 0
    
    def _build_runtime_config(self, slot_id: int, metadata: SlotMetadata) -> Dict[str, Any]:
        """Build runtime configuration with Nova's environment variable precedence"""
        config = {}
        
        # Base configuration from metadata
        if hasattr(metadata, '__dict__'):
            config.update(metadata.__dict__)
        
        # PRESERVE Nova's environment variable pattern
        env_overrides = self._extract_env_overrides(slot_id)
        config.update(env_overrides)
        
        # PRESERVE Nova's SystemConfig integration
        if self.system_config:
            system_overrides = self._extract_system_config_overrides(slot_id)
            config.update(system_overrides)
        
        # Validate configuration
        if not metadata.validate_schema(config):
            logger.warning(f"Configuration validation failed for Slot {slot_id}")
        
        return config
    
    def _extract_env_overrides(self, slot_id: int) -> Dict[str, Any]:
        """Extract environment variable overrides - PRESERVES Nova's pattern"""
        overrides = {}
        
        # Nova's existing patterns
        prefixes = [
            f"NOVA_SLOT{slot_id:02d}_",  # NOVA_SLOT06_
            f"NOVA_SLOT{slot_id}_",      # NOVA_SLOT6_
            f"SLOT{slot_id}_",           # SLOT6_
        ]
        
        for prefix in prefixes:
            for key, value in os.environ.items():
                if key.startswith(prefix):
                    config_key = key[len(prefix):].lower()
                    overrides[config_key] = self._parse_env_value(value)
        
        return overrides
    
    def _extract_system_config_overrides(self, slot_id: int) -> Dict[str, Any]:
        """Extract overrides from Nova's existing SystemConfig"""
        if not self.system_config:
            return {}
        
        overrides = {}
        
        # Map Nova's existing configuration to slot-specific settings
        if slot_id == 4:  # TRI Engine
            if hasattr(self.system_config, 'TRUTH_THRESHOLD'):
                overrides['truth_threshold'] = self.system_config.TRUTH_THRESHOLD
        
        if slot_id == 6:  # Cultural Synthesis
            if hasattr(self.system_config, 'CULTURAL_WEIGHTS'):
                overrides['cultural_weights'] = self.system_config.CULTURAL_WEIGHTS
        
        if slot_id == 9:  # Distortion Protection
            if hasattr(self.system_config, 'DISTORTION_DETECTION_SENSITIVITY'):
                overrides['detection_sensitivity'] = self.system_config.DISTORTION_DETECTION_SENSITIVITY
        
        return overrides
    
    def _parse_env_value(self, value: str) -> Any:
        """Parse environment variable value to appropriate type"""
        # Boolean
        if value.lower() in ('true', 'false'):
            return value.lower() == 'true'
        
        # Float
        try:
            if '.' in value:
                return float(value)
        except ValueError:
            pass
        
        # Int
        try:
            return int(value)
        except ValueError:
            pass
        
        # String (default)
        return value
    
    def _setup_config_watcher(self) -> None:
        """Setup file system watcher for hot-reload"""
        class ConfigChangeHandler(FileSystemEventHandler):
            def __init__(self, manager):
                self.manager = manager
            
            def on_modified(self, event):
                if not event.is_directory and event.src_path.endswith(('.yaml', '.yml')):
                    asyncio.create_task(self.manager._handle_config_change(event.src_path))
        
        self._observer = Observer()
        self._observer.schedule(
            ConfigChangeHandler(self), 
            str(self.config_dir), 
            recursive=True
        )
        self._observer.start()
        logger.info("Configuration hot-reload enabled")
    
    async def _handle_config_change(self, config_path: str) -> None:
        """Handle configuration file changes"""
        try:
            with self._lock:
                path = Path(config_path)
                slot_id = self._extract_slot_id(path.parent.name)
                
                if slot_id in self.slot_metadata:
                    old_metadata = self.slot_metadata[slot_id]
                    old_config = self.runtime_configs[slot_id].copy()
                    
                    # Reload metadata
                    new_metadata = SlotMetadata.from_yaml(config_path)
                    new_config = self._build_runtime_config(slot_id, new_metadata)
                    
                    self.slot_metadata[slot_id] = new_metadata
                    self.runtime_configs[slot_id] = new_config
                    
                    # Notify listeners
                    await self._notify_config_change(slot_id, old_config, new_config)
                    
                    logger.info(f"Hot-reloaded configuration for Slot {slot_id}")
        
        except Exception as e:
            logger.error(f"Failed to handle config change for {config_path}: {e}")
    
    async def _notify_config_change(self, slot_id: int, old_config: Dict, new_config: Dict) -> None:
        """Notify registered listeners of configuration changes"""
        for listener in self.config_listeners:
            try:
                if asyncio.iscoroutinefunction(listener):
                    await listener(slot_id, old_config, new_config)
                else:
                    listener(slot_id, old_config, new_config)
            except Exception as e:
                logger.error(f"Config change listener failed: {e}")
    
    def register_config_listener(self, listener: Callable) -> None:
        """Register listener for configuration changes"""
        self.config_listeners.append(listener)
    
    def get_slot_config(self, slot_id: int, 
                       overrides: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Get configuration for specific slot with Nova's precedence rules"""
        with self._lock:
            base_config = self.runtime_configs.get(slot_id, {}).copy()
            
            if overrides:
                base_config.update(overrides)
            
            return base_config
    
    def get_slot_metadata(self, slot_id: int) -> Optional[SlotMetadata]:
        """Get metadata for specific slot"""
        return self.slot_metadata.get(slot_id)
    
    def list_slots(self) -> List[int]:
        """List all configured slot IDs"""
        return list(self.slot_metadata.keys())
    
    def export_config(self, slot_id: int) -> Dict[str, Any]:
        """Export complete configuration for debugging"""
        metadata = self.slot_metadata.get(slot_id)
        runtime_config = self.runtime_configs.get(slot_id, {})
        
        return {
            'slot_id': slot_id,
            'metadata': metadata.__dict__ if metadata else None,
            'runtime_config': runtime_config,
            'timestamp': datetime.now().isoformat()
        }
    
    async def shutdown(self) -> None:
        """Shutdown configuration manager"""
        if self._observer:
            self._observer.stop()
            self._observer.join()
        logger.info("Configuration manager shutdown complete")

# Global instance - initialized once
_global_config_manager: Optional[EnhancedConfigManager] = None

async def get_config_manager() -> EnhancedConfigManager:
    """Get or create global configuration manager"""
    global _global_config_manager
    if _global_config_manager is None:
        _global_config_manager = EnhancedConfigManager()
        await _global_config_manager.initialize()
    return _global_config_manager

# Convenience functions for Nova integration
def get_slot_config(slot_id: int, **overrides) -> Dict[str, Any]:
    """Synchronous wrapper for getting slot configuration"""
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # If we're in an async context, we need to handle this differently
            manager = _global_config_manager
            if manager is None:
                return {}
            return manager.get_slot_config(slot_id, overrides)
        else:
            manager = loop.run_until_complete(get_config_manager())
            return manager.get_slot_config(slot_id, overrides)
    except Exception as e:
        logger.error(f"Failed to get slot config: {e}")
        return {}

if __name__ == "__main__":
    # Example usage
    async def main():
        config_manager = await get_config_manager()

        # Get Slot 6 configuration with Nova's environment variable precedence
        slot6_config = config_manager.get_slot_config(6)
        print("Slot 6 Configuration:", slot6_config)

        # Register for configuration changes
        def on_config_change(slot_id, old_config, new_config):
            print(f"Slot {slot_id} configuration changed")

        config_manager.register_config_listener(on_config_change)

        # Export debug information
        debug_info = config_manager.export_config(6)
        print("Debug Info:", debug_info)

    asyncio.run(main())

