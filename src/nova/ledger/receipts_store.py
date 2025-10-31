"""Append-only receipt store for federation events."""

from __future__ import annotations

import json
import threading
from pathlib import Path
from typing import Any, Dict, Iterable, Optional


class ReceiptsStore:
    """Persist receipts to memory and optional newline-delimited JSON file."""

    def __init__(self, path: Optional[Path] = None) -> None:
        self._path = path
        self._lock = threading.Lock()
        self._entries: list[Dict[str, Any]] = []
        if path and path.exists():
            for line in path.read_text(encoding="utf-8").splitlines():
                line = line.strip()
                if not line:
                    continue
                try:
                    self._entries.append(json.loads(line))
                except json.JSONDecodeError:
                    continue

    def append(self, payload: Dict[str, Any]) -> None:
        """Append a receipt payload."""
        data = dict(payload)
        with self._lock:
            self._entries.append(data)
            if self._path:
                self._path.parent.mkdir(parents=True, exist_ok=True)
                with self._path.open("a", encoding="utf-8") as handle:
                    handle.write(json.dumps(data, sort_keys=True) + "\n")

    def entries(self) -> Iterable[Dict[str, Any]]:
        return tuple(self._entries)

    def clear(self) -> None:
        with self._lock:
            self._entries.clear()
            if self._path:
                self._path.write_text("", encoding="utf-8")


__all__ = ["ReceiptsStore"]
