# ruff: noqa: E402
from src_bootstrap import ensure_src_on_path
ensure_src_on_path()
import logging
from typing import Any, Dict, List

try:
    from nova.slots.slot05_constellation.constellation_engine import ConstellationEngine
    ENGINE = ConstellationEngine()
    AVAILABLE = True
except Exception as exc:  # pragma: no cover - optional slot
    logging.getLogger(__name__).exception(
        "Failed to import Slot 5 constellation engine: %s", exc
    )
    ENGINE = None
    AVAILABLE = False

logger = logging.getLogger(__name__)


class Slot5ConstellationAdapter:
    """Enhanced adapter for Slot-5 Constellation engine with link computation and stability metrics.

    Provides orchestration interface for constellation mapping with:
    - Item positioning and analysis
    - Link computation between related items
    - Stability metrics and historical tracking
    - Connectivity analysis
    """

    def __init__(self) -> None:
        self.available = AVAILABLE
        self._engine = ENGINE

    def map(self, items: list[str]) -> Dict[str, Any]:
        """Map items into constellation with links and stability metrics.

        Args:
            items: List of items to map

        Returns:
            Dict with constellation, links, stability, and metadata
        """
        if not self.available or not self._engine:
            logger.warning("Constellation engine not available")
            return {
                "constellation": [],
                "links": [],
                "stability": {"score": 0.0, "status": "unavailable"},
                "error": "Engine not available"
            }

        try:
            result = self._engine.map(items)
            logger.debug(f"Mapped constellation: {len(items)} items -> "
                        f"{len(result.get('links', []))} links, "
                        f"stability: {result.get('stability', {}).get('score', 0):.3f}")
            return result
        except Exception as exc:  # pragma: no cover - defensive
            logger.exception("Constellation mapping failed: %s", exc)
            return {
                "constellation": [],
                "links": [],
                "stability": {"score": 0.0, "status": "error"},
                "error": str(exc)
            }

    def get_configuration(self) -> Dict[str, Any]:
        """Get current engine configuration parameters.

        Returns:
            Dict with similarity thresholds and stability settings
        """
        if not self.available or not self._engine:
            return {}

        return {
            "similarity_threshold": self._engine.similarity_threshold,
            "link_strength_threshold": self._engine.link_strength_threshold,
            "stability_window": self._engine.stability_window,
            "version": self._engine.__version__
        }

    def update_configuration(self, config: Dict[str, Any]) -> bool:
        """Update engine configuration parameters.

        Args:
            config: Dict with configuration parameters to update

        Returns:
            True if update successful, False otherwise
        """
        if not self.available or not self._engine:
            return False

        try:
            if "similarity_threshold" in config:
                self._engine.similarity_threshold = float(config["similarity_threshold"])
            if "link_strength_threshold" in config:
                self._engine.link_strength_threshold = float(config["link_strength_threshold"])
            if "stability_window" in config:
                self._engine.stability_window = int(config["stability_window"])
            return True
        except (ValueError, TypeError) as exc:
            logger.error(f"Configuration update failed: {exc}")
            return False

    def get_stability_history(self) -> List[Dict[str, Any]]:
        """Get constellation stability history.

        Returns:
            List of historical stability entries
        """
        if not self.available or not self._engine:
            return []

        return list(self._engine._constellation_history)

    def health_check(self) -> Dict[str, Any]:
        """Perform adapter health check.

        Returns:
            Dict with health status and metrics
        """
        return {
            "available": self.available,
            "engine_loaded": self._engine is not None,
            "version": self._engine.__version__ if self._engine else None,
            "history_entries": len(self._engine._constellation_history) if self._engine else 0,
            "status": "healthy" if self.available and self._engine else "degraded"
        }
