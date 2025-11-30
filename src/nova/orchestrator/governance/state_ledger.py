from __future__ import annotations

import hashlib
import json
import time
from typing import Any, Dict, List


class GovernanceLedger:
    """In-memory hash-chained ledger for governance snapshots."""

    def __init__(self) -> None:
        self._entries: List[Dict[str, Any]] = []
        self._last_hash = ""

    def append(self, entry: Dict[str, Any]) -> None:
        payload = {
            "timestamp": time.time(),
            "entry": entry,
            "prev_hash": self._last_hash,
        }
        serialized = json.dumps(payload, sort_keys=True).encode("utf-8")
        payload_hash = hashlib.blake2b(serialized, digest_size=16).hexdigest()
        payload["hash"] = payload_hash
        self._entries.append(payload)
        self._last_hash = payload_hash

    def snapshot(self) -> List[Dict[str, Any]]:
        return list(self._entries)
