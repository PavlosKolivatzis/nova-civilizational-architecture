from typing import Any


class Slot4TRIAdapter:
    """Minimal stub for the Slot-4 TRI adapter used in tests."""

    available: bool = True

    async def calibrate(self, payload: Any) -> None:  # pragma: no cover - trivial
        return None
