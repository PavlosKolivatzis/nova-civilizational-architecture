from __future__ import annotations
from dataclasses import dataclass
from typing import Callable, Optional

@dataclass
class SnapshotSet:
    slot10_id: str
    slot08_id: str
    slot04_id: str

class SnapshotBackout:
    """Coordinate cross-slot snapshot rollback to a consistent point."""
    def __init__(self):
        self._set: Optional[SnapshotSet] = None

    def record_promotion(self, *, slot10_id: str, slot08_id: str, slot04_id: str) -> SnapshotSet:
        self._set = SnapshotSet(slot10_id=slot10_id, slot08_id=slot08_id, slot04_id=slot04_id)
        return self._set

    def rollback(
        self,
        app_restore: Callable[[str], bool],
        slot8_restore: Callable[[str], bool],
        slot4_restore: Callable[[str], bool],
    ) -> bool:
        if not self._set:
            return False
        ok10 = bool(app_restore(self._set.slot10_id))
        ok8 = bool(slot8_restore(self._set.slot08_id))
        ok4 = bool(slot4_restore(self._set.slot04_id))
        return ok10 and ok8 and ok4