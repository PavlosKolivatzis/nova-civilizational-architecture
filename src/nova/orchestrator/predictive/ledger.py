"""Predictive foresight ledger (Phase-7)."""

from __future__ import annotations

import hashlib
import json
from copy import deepcopy
from typing import Any, Dict, List


class PredictiveLedgerError(Exception):
    """Raised when foresight ledger invariants are violated."""


class PredictiveLedger:
    """Append-only, hash-chained ledger for predictive consistency snapshots."""

    def __init__(self):
        self._entries: List[Dict[str, Any]] = []

    def append(self, payload: Dict[str, Any]) -> None:
        """Append a new foresight snapshot ensuring monotonic timestamps."""
        if "timestamp" not in payload:
            raise PredictiveLedgerError("Predictive ledger entries require 'timestamp'")

        timestamp = float(payload["timestamp"])
        if self._entries and timestamp <= self._entries[-1]["timestamp"]:
            raise PredictiveLedgerError("Predictive ledger timestamps must be strictly increasing")

        prev_hash = self._entries[-1]["hash"] if self._entries else ""
        entry = {
            "timestamp": timestamp,
            "entry": dict(payload),
            "prev_hash": prev_hash,
        }
        serialized = json.dumps(entry, sort_keys=True, default=str).encode("utf-8")
        entry["hash"] = hashlib.sha3_256(serialized).hexdigest()
        self._entries.append(entry)

    def snapshot(self) -> List[Dict[str, Any]]:
        """Return a copy of all ledger entries."""
        return [deepcopy(entry) for entry in self._entries]

    def head(self) -> Dict[str, Any] | None:
        """Return the most recent ledger entry."""
        return deepcopy(self._entries[-1]) if self._entries else None
