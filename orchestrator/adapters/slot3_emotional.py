import logging
from typing import Any, Dict

try:
    from slots.slot03_emotional_matrix.emotional_matrix_engine import EmotionalMatrixEngine
    ENGINE = EmotionalMatrixEngine()
    AVAILABLE = True
except Exception as exc:  # pragma: no cover - optional slot
    logging.getLogger(__name__).exception(
        "Failed to import Slot 3 emotional matrix engine: %s", exc
    )
    ENGINE = None
    AVAILABLE = False


class Slot3EmotionalAdapter:
    """Adapter wrapper for the Slot-3 Emotional Matrix engine."""

    def __init__(self) -> None:
        self.available = AVAILABLE

    def analyze(self, content: str) -> Dict[str, Any]:
        if not self.available or not ENGINE:
            return {}
        try:
            return ENGINE.analyze(content)
        except Exception as exc:  # pragma: no cover - defensive
            logging.getLogger(__name__).exception(
                "Emotional analysis failed: %s", exc
            )
            return {}
