"""Truth Anchor Engine v1.2.0.

Provides lightweight management of immutable "truth" anchors used across
slots. Each anchor is stored with optional backup metadata and operations
update internal metrics for observability. The engine performs best-effort
recovery when anchors are missing or corrupted and logs all operations.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Optional
import logging


@dataclass
class AnchorRecord:
    """In-memory representation of an anchor."""

    value: Any
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class EngineMetrics:
    """Simple metrics container for observability."""

    lookups: int = 0
    recoveries: int = 0
    failures: int = 0


class TruthAnchorEngine:
    """Core engine for truth anchor management (v1.2.0)."""

    VERSION = "1.2.0"

    def __init__(self) -> None:
        self._anchors: Dict[str, AnchorRecord] = {}
        self.metrics = EngineMetrics()
        self.logger = logging.getLogger("truth_anchor_engine")
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            handler.setFormatter(
                logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
            )
            self.logger.addHandler(handler)
        self.logger.setLevel(logging.INFO)

    # ------------------------------------------------------------------
    # Anchor management
    # ------------------------------------------------------------------
    def register(self, anchor_id: str, value: Any, **metadata: Any) -> None:
        """Register ``value`` under ``anchor_id`` with optional metadata."""
        self._anchors[anchor_id] = AnchorRecord(value=value, metadata=metadata)
        self.logger.debug("Anchor registered: %s", anchor_id)

    def verify(self, anchor_id: str, value: Any) -> bool:
        """Validate ``value`` against a stored anchor.

        Returns ``True`` if the anchor exists and matches ``value``. If the
        anchor is missing or mismatched a recovery attempt is made using
        stored backup data and the result is logged.
        """
        self.metrics.lookups += 1
        record = self._anchors.get(anchor_id)
        if record and record.value == value:
            return True

        self.metrics.failures += 1
        self.logger.warning("Anchor mismatch or missing: %s", anchor_id)
        recovered = self._recover(anchor_id)
        return recovered == value if recovered is not None else False

    def _recover(self, anchor_id: str) -> Optional[Any]:
        """Attempt best-effort recovery for ``anchor_id``.

        Recovery uses a ``backup`` field in the anchor metadata if present.
        """
        record = self._anchors.get(anchor_id)
        backup = record.metadata.get("backup") if record else None
        if backup is not None:
            self.metrics.recoveries += 1
            self.logger.info("Recovered anchor %s from backup", anchor_id)
            # promote backup to active value
            if record:
                record.value = backup
            else:
                self._anchors[anchor_id] = AnchorRecord(value=backup)
            return backup
        self.logger.error("Failed to recover anchor: %s", anchor_id)
        return None

    # ------------------------------------------------------------------
    # Metrics / Introspection
    # ------------------------------------------------------------------
    def snapshot(self) -> Dict[str, Any]:
        """Return a snapshot of the engine state and metrics."""
        return {
            "version": self.VERSION,
            "anchors": len(self._anchors),
            "lookups": self.metrics.lookups,
            "recoveries": self.metrics.recoveries,
            "failures": self.metrics.failures,
        }


__all__ = ["TruthAnchorEngine", "AnchorRecord", "EngineMetrics"]
