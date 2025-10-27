"""
Ledger client for slot emitters.

Phase 13 RUN 13-2: Thin client for slots to emit ledger records.
"""

from __future__ import annotations

import logging
from typing import Dict, Optional

from .model import RecordKind
from .store import LedgerStore


class LedgerClient:
    """
    Client for emitting ledger records from slots.

    Provides a simple interface for slots to append records without
    managing store lifecycle or continuity logic.
    """

    _instance: Optional[LedgerClient] = None
    _shared_store: Optional[LedgerStore] = None

    def __init__(self, store: Optional[LedgerStore] = None, logger: Optional[logging.Logger] = None):
        """Initialize ledger client."""
        self.logger = logger or logging.getLogger("ledger.client")

        # Use class-level shared store if not explicitly provided
        if store is not None:
            self._store = store
        elif LedgerClient._shared_store is None:
            # First instance creates the shared store
            LedgerClient._shared_store = LedgerStore(logger=self.logger)
            self._store = LedgerClient._shared_store
        else:
            # Subsequent instances reuse the shared store
            self._store = LedgerClient._shared_store

    @classmethod
    def get_instance(cls) -> LedgerClient:
        """Get singleton instance of ledger client."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def append_record(
        self,
        anchor_id: str,
        slot: str,
        kind: RecordKind | str,
        payload: Dict,
        producer: str = "unknown",
        version: str = "unknown",
        sig: Optional[bytes] = None,
    ) -> bool:
        """
        Append a record to the ledger.

        Args:
            anchor_id: Truth anchor ID
            slot: Slot identifier (e.g., "01", "02", "08")
            kind: Record kind (event type)
            payload: Event-specific data
            producer: Service that created the record
            version: Software version
            sig: Optional PQC signature

        Returns:
            True if append succeeded, False otherwise
        """
        try:
            # Convert string kind to enum if needed
            if isinstance(kind, str):
                kind = RecordKind(kind)

            record = self._store.append(
                anchor_id=anchor_id,
                slot=slot,
                kind=kind,
                payload=payload,
                producer=producer,
                version=version,
                sig=sig,
            )

            self.logger.debug(
                f"Appended ledger record: anchor={anchor_id}, slot={slot}, "
                f"kind={kind.value}, rid={record.rid}"
            )
            return True

        except Exception as e:
            self.logger.error(f"Failed to append ledger record: {e}", exc_info=True)
            return False

    def get_store(self) -> LedgerStore:
        """Get underlying ledger store (for testing/debugging)."""
        return self._store
