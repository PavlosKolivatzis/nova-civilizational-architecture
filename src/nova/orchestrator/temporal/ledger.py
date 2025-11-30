"""Temporal ledger implementation (Phase-6 scaffold)."""

from __future__ import annotations

import hashlib
import json
from typing import Any, Dict, List


class TemporalLedgerError(Exception):
    """Base exception for temporal ledger failures."""


class TemporalLedger:
    """Append-only hash-chained ledger for temporal snapshots."""

    def __init__(self) -> None:
        self._entries: List[Dict[str, Any]] = []

    def append(self, payload: Dict[str, Any]) -> None:
        """Append a new temporal snapshot enforcing monotonic time + hash chaining."""
        if "timestamp" not in payload:
            raise TemporalLedgerError("Temporal ledger entries require a 'timestamp'")

        timestamp = float(payload["timestamp"])
        if self._entries and timestamp <= self._entries[-1]["timestamp"]:
            raise TemporalLedgerError("Temporal ledger timestamps must be strictly increasing")

        prev_hash = self._entries[-1]["hash"] if self._entries else ""
        entry = {
            "timestamp": timestamp,
            "entry": dict(payload),
            "prev_hash": prev_hash,
        }
        serialized = json.dumps(entry, sort_keys=True, default=str).encode("utf-8")
        entry_hash = hashlib.sha3_256(serialized).hexdigest()
        entry["hash"] = entry_hash
        self._entries.append(entry)

    def snapshot(self) -> List[Dict[str, Any]]:
        """Return a copy of the ledger entries."""
        return [dict(entry) for entry in self._entries]

    def head(self) -> Dict[str, Any] | None:
        """Return the last entry if present."""
        return dict(self._entries[-1]) if self._entries else None
