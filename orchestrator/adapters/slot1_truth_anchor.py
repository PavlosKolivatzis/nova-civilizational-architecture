import logging
from typing import Any, Dict

try:
    from slots.slot01_truth_anchor.truth_anchor_engine import TruthAnchorEngine

    ENGINE = TruthAnchorEngine()
    AVAILABLE = True
except Exception as exc:  # pragma: no cover - optional slot
    logging.getLogger(__name__).exception(
        "Failed to import Slot 1 truth anchor engine: %s", exc
    )
    ENGINE = None
    AVAILABLE = False


class Slot1TruthAnchorAdapter:
    """Adapter wrapper for the Slot-1 Truth Anchor engine."""

    def __init__(self) -> None:
        self.available = AVAILABLE

    def register(self, anchor_id: str, value: Any, **metadata: Any) -> None:
        if not self.available or not anchor_id:
            return
        try:
            if hasattr(ENGINE, "establish_anchor"):
                ENGINE.establish_anchor(anchor_id, value, **metadata)
            else:
                ENGINE.register(anchor_id, value, **metadata)
        except Exception as exc:  # pragma: no cover - defensive
            logging.getLogger(__name__).exception(
                "Anchor registration failed: %s", exc
            )

    def verify(self, anchor_id: str, value: Any) -> bool:
        if not self.available or not anchor_id:
            return True
        try:
            if hasattr(ENGINE, "verify_anchor"):
                return ENGINE.verify_anchor(anchor_id, value)
            return ENGINE.verify(anchor_id, value)
        except Exception as exc:  # pragma: no cover - defensive
            logging.getLogger(__name__).exception(
                "Anchor verification failed: %s", exc
            )
            return False

    def snapshot(self) -> Dict[str, Any]:
        if not self.available:
            return {}
        try:
            if hasattr(ENGINE, "list_anchors"):
                return ENGINE.list_anchors()
            return ENGINE.snapshot()
        except Exception:  # pragma: no cover - defensive
            return {}
