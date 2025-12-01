# ruff: noqa: E402
from src_bootstrap import ensure_src_on_path
ensure_src_on_path()
"""Enhanced Slot 5 Constellation Adapter with Processual-level capabilities.

This adapter provides the orchestration interface for the enhanced constellation engine,
enabling adaptive processing and cross-slot coordination.
"""

import logging
from typing import Any, Dict, List, Optional

try:
    from nova.slots.slot05_constellation.enhanced_constellation_engine import EnhancedConstellationEngine
    from nova.orchestrator.semantic_mirror import get_semantic_mirror

    # Initialize with semantic mirror for cross-slot coordination
    semantic_mirror = get_semantic_mirror()
    ENGINE = EnhancedConstellationEngine(semantic_mirror)
    ENGINE_TYPE = "enhanced"
    AVAILABLE = True
except ImportError:
    try:
        # Fallback to base engine
        from nova.slots.slot05_constellation.constellation_engine import ConstellationEngine
        ENGINE = ConstellationEngine()
        ENGINE_TYPE = "base"
        AVAILABLE = True
    except ImportError:
        ENGINE = None
        ENGINE_TYPE = "none"
        AVAILABLE = False
except Exception as exc:
    logging.getLogger(__name__).exception(
        "Failed to import Slot 5 enhanced constellation engine: %s", exc
    )
    ENGINE = None
    ENGINE_TYPE = "error"
    AVAILABLE = False

logger = logging.getLogger(__name__)


class EnhancedSlot5ConstellationAdapter:
    """Enhanced adapter for Slot 5 Constellation engine with adaptive capabilities.

    Provides Processual-level orchestration interface with:
    - Adaptive threshold management
    - Context-aware processing
    - Cross-slot coordination via semantic mirror
    - Performance-based optimization
    - Real-time adaptation capabilities
    """

    def __init__(self) -> None:
        self.available = AVAILABLE
        self._engine = ENGINE
        self.engine_type = ENGINE_TYPE

    def map(self, items: List[str], context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Enhanced constellation mapping with adaptive processing.

        Args:
            items: List of items to map
            context: Optional context for adaptive processing

        Returns:
            Enhanced constellation mapping with adaptive metrics
        """
        if not self.available or not self._engine:
            logger.warning("Enhanced constellation engine not available")
            return {
                "constellation": [],
                "links": [],
                "stability": {"score": 0.0, "status": "unavailable"},
                "adaptive": {"enabled": False},
                "error": "Engine not available"
            }

        try:
            # Use enhanced mapping if available
            if hasattr(self._engine, 'map') and self.engine_type == "enhanced":
                result = self._engine.map(items, context)
                logger.debug(f"Enhanced constellation mapping: {len(items)} items -> "
                           f"{len(result.get('links', []))} links, "
                           f"stability: {result.get('stability', {}).get('score', 0):.3f}, "
                           f"adaptive: {result.get('adaptive', {}).get('processing_time', 0):.3f}s")
            else:
                # Fallback to base mapping
                result = self._engine.map(items)
                result['adaptive'] = {"enabled": False, "engine_type": self.engine_type}
                logger.debug(f"Base constellation mapping: {len(items)} items -> "
                           f"{len(result.get('links', []))} links")

            return result

        except Exception as exc:
            logger.exception("Enhanced constellation mapping failed: %s", exc)
            return {
                "constellation": [],
                "links": [],
                "stability": {"score": 0.0, "status": "error"},
                "adaptive": {"enabled": False, "error": str(exc)},
                "error": str(exc)
            }

    def get_adaptive_metrics(self) -> Dict[str, Any]:
        """Get adaptive processing metrics.

        Returns:
            Dict with adaptation statistics and performance metrics
        """
        if not self.available or not self._engine:
            return {"available": False}

        if hasattr(self._engine, 'get_adaptive_metrics'):
            try:
                metrics = self._engine.get_adaptive_metrics()
                metrics['engine_type'] = self.engine_type
                return metrics
            except Exception as exc:
                logger.error(f"Failed to get adaptive metrics: {exc}")
                return {"error": str(exc), "engine_type": self.engine_type}
        else:
            return {"adaptive_enabled": False, "engine_type": self.engine_type}

    def get_configuration(self) -> Dict[str, Any]:
        """Get current engine configuration including adaptive thresholds.

        Returns:
            Dict with current configuration and adaptive state
        """
        if not self.available or not self._engine:
            return {"available": False}

        config = {
            "engine_type": self.engine_type,
            "version": getattr(self._engine, '__version__', 'unknown')
        }

        # Get adaptive thresholds if available
        if hasattr(self._engine, 'adaptive_processor'):
            try:
                adaptive_thresholds = self._engine.adaptive_processor.get_current_thresholds()
                config['adaptive_thresholds'] = adaptive_thresholds
                config['adaptive_enabled'] = True
            except Exception as exc:
                logger.error(f"Failed to get adaptive thresholds: {exc}")
                config['adaptive_error'] = str(exc)
        else:
            # Fallback to base engine configuration
            if hasattr(self._engine, 'similarity_threshold'):
                config.update({
                    "similarity_threshold": self._engine.similarity_threshold,
                    "link_strength_threshold": getattr(self._engine, 'link_strength_threshold', 0.2),
                    "stability_window": getattr(self._engine, 'stability_window', 10),
                    "adaptive_enabled": False
                })

        return config

    def update_configuration(self, config: Dict[str, Any]) -> bool:
        """Update engine configuration including adaptive parameters.

        Args:
            config: Dict with configuration parameters to update

        Returns:
            True if update successful, False otherwise
        """
        if not self.available or not self._engine:
            return False

        try:
            success = True

            # Update adaptive processor if available
            if hasattr(self._engine, 'adaptive_processor') and 'adaptive_config' in config:
                adaptive_config = config['adaptive_config']
                processor = self._engine.adaptive_processor

                if 'learning_rate' in adaptive_config:
                    processor.learning_rate = float(adaptive_config['learning_rate'])
                if 'adaptation_sensitivity' in adaptive_config:
                    processor.adaptation_sensitivity = float(adaptive_config['adaptation_sensitivity'])

            # Update base engine configuration
            if hasattr(self._engine, 'similarity_threshold') and "similarity_threshold" in config:
                self._engine.similarity_threshold = float(config["similarity_threshold"])
            if hasattr(self._engine, 'link_strength_threshold') and "link_strength_threshold" in config:
                self._engine.link_strength_threshold = float(config["link_strength_threshold"])
            if hasattr(self._engine, 'stability_window') and "stability_window" in config:
                self._engine.stability_window = int(config["stability_window"])

            logger.info(f"Configuration updated for {self.engine_type} constellation engine")
            return success

        except (ValueError, TypeError) as exc:
            logger.error(f"Configuration update failed: {exc}")
            return False

    def reset_adaptive_state(self) -> bool:
        """Reset adaptive processing state to defaults.

        Returns:
            True if reset successful, False otherwise
        """
        if not self.available or not self._engine:
            return False

        if hasattr(self._engine, 'reset_adaptive_state'):
            try:
                self._engine.reset_adaptive_state()
                logger.info("Adaptive state reset successfully")
                return True
            except Exception as exc:
                logger.error(f"Adaptive state reset failed: {exc}")
                return False
        else:
            logger.warning("Adaptive state reset not supported by base engine")
            return False

    def enable_cross_slot_coordination(self) -> bool:
        """Enable cross-slot coordination via semantic mirror.

        Returns:
            True if coordination enabled, False otherwise
        """
        if not self.available or not self._engine:
            return False

        if hasattr(self._engine, 'enable_cross_slot_coordination'):
            try:
                from nova.orchestrator.semantic_mirror import get_semantic_mirror
                semantic_mirror = get_semantic_mirror()
                self._engine.enable_cross_slot_coordination(semantic_mirror)
                logger.info("Cross-slot coordination enabled")
                return True
            except Exception as exc:
                logger.error(f"Failed to enable cross-slot coordination: {exc}")
                return False
        else:
            logger.warning("Cross-slot coordination not supported by base engine")
            return False

    def get_stability_history(self) -> List[Dict[str, Any]]:
        """Get constellation stability history.

        Returns:
            List of historical stability entries
        """
        if not self.available or not self._engine:
            return []

        # Try enhanced engine first
        if hasattr(self._engine, 'base_engine') and hasattr(self._engine.base_engine, '_constellation_history'):
            return list(self._engine.base_engine._constellation_history)
        elif hasattr(self._engine, '_constellation_history'):
            return list(self._engine._constellation_history)
        else:
            return []

    def health_check(self) -> Dict[str, Any]:
        """Perform comprehensive adapter health check.

        Returns:
            Dict with health status and detailed metrics
        """
        health = {
            "available": self.available,
            "engine_loaded": self._engine is not None,
            "engine_type": self.engine_type,
            "version": getattr(self._engine, '__version__', None) if self._engine else None,
        }

        if self._engine:
            # Basic health
            if hasattr(self._engine, '_constellation_history'):
                health["history_entries"] = len(self._engine._constellation_history)
            elif hasattr(self._engine, 'base_engine') and hasattr(self._engine.base_engine, '_constellation_history'):
                health["history_entries"] = len(self._engine.base_engine._constellation_history)
            else:
                health["history_entries"] = 0

            # Enhanced health checks
            if hasattr(self._engine, 'get_adaptive_metrics'):
                try:
                    adaptive_metrics = self._engine.get_adaptive_metrics()
                    health["adaptive_metrics"] = adaptive_metrics
                    health["adaptive_enabled"] = True
                except Exception as exc:
                    health["adaptive_error"] = str(exc)
                    health["adaptive_enabled"] = False
            else:
                health["adaptive_enabled"] = False

            # Cross-slot coordination status
            if hasattr(self._engine, 'semantic_mirror'):
                health["cross_slot_coordination"] = self._engine.semantic_mirror is not None
            else:
                health["cross_slot_coordination"] = False

            # Overall status
            if health["adaptive_enabled"] and health["cross_slot_coordination"]:
                health["status"] = "processual"  # Full 4.0 capabilities
            elif health["adaptive_enabled"]:
                health["status"] = "structural+"  # Enhanced 3.5+ capabilities
            else:
                health["status"] = "structural"   # Base 3.0 capabilities
        else:
            health["status"] = "unavailable"

        return health
