from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Optional, Dict
import time

from .policy import Slot10Policy


@dataclass
class SnapshotSet:
    slot10_id: str
    slot08_id: str
    slot04_id: str
    ts_ms: int
    reason: str = "promotion"


@dataclass
class RollbackResult:
    success: bool
    slot10_success: bool
    slot08_success: bool
    slot04_success: bool
    execution_time_s: float
    errors: Dict[str, str]


class SnapshotBackout:
    """Coordinates cross-slot snapshot backout with MTTR validation."""

    def __init__(self, policy: Optional[Slot10Policy] = None):
        self.policy = policy or Slot10Policy()
        self._current: Optional[SnapshotSet] = None

    def record_promotion(
        self,
        *,
        slot10_id: str,
        slot08_id: str,
        slot04_id: str,
        reason: str = "promotion",
    ) -> SnapshotSet:
        ss = SnapshotSet(
            slot10_id=slot10_id,
            slot08_id=slot08_id,
            slot04_id=slot04_id,
            ts_ms=int(time.time() * 1000),
            reason=reason,
        )
        self._current = ss
        return ss

    def last_snapshot_set(self) -> Optional[SnapshotSet]:
        return self._current

    def rollback(
        self,
        app_restore: Callable[[str], bool],
        slot8_restore: Callable[[str], bool],
        slot4_restore: Callable[[str], bool],
    ) -> RollbackResult:
        if not self._current:
            return RollbackResult(
                success=False,
                slot10_success=False,
                slot08_success=False,
                slot04_success=False,
                execution_time_s=0.0,
                errors={"snapshots": "No snapshot set recorded"},
            )

        start = time.time()
        errors: Dict[str, str] = {}

        s10_ok = app_restore(self._current.slot10_id)
        if not s10_ok:
            errors["slot10"] = "Failed to restore application snapshot"

        s8_ok = slot8_restore(self._current.slot08_id)
        if not s8_ok:
            errors["slot08"] = "Failed to restore memory lock"

        s4_ok = slot4_restore(self._current.slot04_id)
        if not s4_ok:
            errors["slot4"] = "Failed to restore TRI model"

        dt = time.time() - start

        # MTTR check (we flag but do not force failure if all restores succeeded)
        if dt > self.policy.rollback_timeout_s:
            errors["mttr"] = f"Rollback exceeded {self.policy.rollback_timeout_s}s timeout (took {dt:.3f}s)"

        success = s10_ok and s8_ok and s4_ok
        return RollbackResult(
            success=success,
            slot10_success=s10_ok,
            slot08_success=s8_ok,
            slot04_success=s4_ok,
            execution_time_s=dt,
            errors=errors,
        )
