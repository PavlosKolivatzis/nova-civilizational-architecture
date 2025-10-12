"""Adapter for Slot 5 - Constellation."""
from typing import Any, Dict

try:
    from .constellation_engine import ConstellationEngine
    ENGINE = ConstellationEngine()
    AVAILABLE = True
except Exception:  # pragma: no cover - optional engine
    ENGINE = None  # type: ignore
    AVAILABLE = False


class Slot5ConstellationAdapter:
    """Minimal adapter around the constellation engine."""

    def __init__(self) -> None:
        self.available = AVAILABLE

    def map(self, items: list[str]) -> Dict[str, Any]:
        if not self.available or not ENGINE:
            return {}
        try:
            return ENGINE.map(items)
        except Exception:  # pragma: no cover - defensive
            return {}
