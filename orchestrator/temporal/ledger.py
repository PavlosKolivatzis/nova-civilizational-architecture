"""Temporal ledger stub."""

from __future__ import annotations

from typing import List, Dict, Any


class TemporalLedger:
    """Placeholder ledger implementation."""

    def __init__(self) -> None:
        self._entries: List[Dict[str, Any]] = []

    def append(self, entry: Dict[str, Any]) -> None:
        self._entries.append(entry)

    def snapshot(self) -> List[Dict[str, Any]]:
        return list(self._entries)
