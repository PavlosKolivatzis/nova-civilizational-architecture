import logging
from typing import Any, Dict

try:
    from slots.slot05_constellation.constellation_engine import ConstellationEngine
    ENGINE = ConstellationEngine()
    AVAILABLE = True
except Exception as exc:  # pragma: no cover - optional slot
    logging.getLogger(__name__).exception(
        "Failed to import Slot 5 constellation engine: %s", exc
    )
    ENGINE = None
    AVAILABLE = False


class Slot5ConstellationAdapter:
    """Adapter wrapper for the Slot-5 Constellation engine."""

    def __init__(self) -> None:
        self.available = AVAILABLE

    def map(self, items: list[str]) -> Dict[str, Any]:
        if not self.available or not ENGINE:
            return {}
        try:
            return ENGINE.map(items)
        except Exception as exc:  # pragma: no cover - defensive
            logging.getLogger(__name__).exception(
                "Constellation mapping failed: %s", exc
            )
            return {}
