from __future__ import annotations
import logging
from typing import Any, Optional, Set

try:
    from nova.slots.slot08_memory_ethics.lock_guard import EthicsGuard, MemoryLock
    AVAILABLE = True
except Exception as exc:  # pragma: no cover - slot optional
    logging.getLogger(__name__).exception(
        "Failed to import Slot 8 memory ethics guard: %s", exc
    )
    AVAILABLE = False

    class MemoryLock:  # type: ignore
        data: Any

    class EthicsGuard:  # type: ignore
        @staticmethod
        def register(*args, **kwargs):
            return None

        @staticmethod
        def read(*args, **kwargs):
            return None

        @staticmethod
        def write(*args, **kwargs):
            return None


class Slot8MemoryEthicsAdapter:
    """Adapter wrapper for Slot-8 memory ethics guard."""

    def __init__(self) -> None:
        self.available = AVAILABLE

    def register(
        self,
        name: str,
        data: Any,
        *,
        actor: str,
        readers: Optional[Set[str]] = None,
        writers: Optional[Set[str]] = None,
    ) -> Optional[MemoryLock]:
        if not self.available:
            return None
        try:
            return EthicsGuard.register(
                name,
                data,
                readers=readers,
                writers=writers,
                actor=actor,
            )
        except Exception:
            logging.getLogger(__name__).exception("Memory registration failed")
            return None

    def read(self, name: str, actor: str) -> Any:
        if not self.available:
            return None
        try:
            return EthicsGuard.read(name, actor)
        except Exception:
            logging.getLogger(__name__).exception("Memory read failed")
            return None

    def write(self, name: str, actor: str, data: Any) -> bool:
        if not self.available:
            return False
        try:
            EthicsGuard.write(name, actor, data)
            return True
        except Exception:
            logging.getLogger(__name__).exception("Memory write failed")
            return False
