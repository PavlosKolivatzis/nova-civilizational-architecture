"""
Ledger storage with append-only semantics and continuity checks.

Phase 13: Autonomous Verification Ledger
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Dict, List, Optional

from .model import LedgerRecord, RecordKind, Checkpoint
from .canon import compute_record_hash, verify_record_hash, compute_merkle_root
from .id_gen import generate_record_id, generate_checkpoint_id
from .metrics import (
    ledger_appends_total,
    ledger_append_duration_seconds,
    ledger_query_total,
    ledger_continuity_breaks_total,
    ledger_records_total,
)


class ContinuityError(Exception):
    """Raised when hash chain continuity is broken."""

    pass


class LedgerStore:
    """
    In-memory ledger store with hash-linked continuity enforcement.

    Provides append-only storage with automatic hash verification and
    prev_hash continuity checking.
    """

    def __init__(self, logger: Optional[logging.Logger] = None):
        """Initialize ledger store."""
        self.logger = logger or logging.getLogger("ledger.store")
        self._records: Dict[str, LedgerRecord] = {}  # rid -> record
        self._anchor_chains: Dict[str, List[str]] = {}  # anchor_id -> [rid...]
        self._checkpoints: Dict[str, Checkpoint] = {}  # cid -> checkpoint

    def append(
        self,
        anchor_id: str,
        slot: str,
        kind: RecordKind,
        payload: Dict,
        producer: str = "unknown",
        version: str = "unknown",
        sig: Optional[bytes] = None,
    ) -> LedgerRecord:
        """
        Append a new record to the ledger with continuity enforcement.

        Args:
            anchor_id: Truth anchor this record pertains to
            slot: Slot ID (e.g., "01", "02", "08")
            kind: Record kind (event type)
            payload: Event-specific data (will be stored as canonical JSON)
            producer: Service that created the record
            version: Software version
            sig: Optional PQC signature

        Returns:
            Created LedgerRecord

        Raises:
            ContinuityError: If prev_hash doesn't match last record for anchor
        """
        with ledger_append_duration_seconds.time():
            # Generate record ID (UUIDv7 for time-ordering)
            rid = generate_record_id()
            ts = datetime.now(timezone.utc)

            # Get previous record hash for this anchor
            prev_hash = self._get_last_hash(anchor_id)

            # Compute record hash
            record_hash = compute_record_hash(
                rid=rid,
                anchor_id=anchor_id,
                slot=slot,
                kind=kind.value if isinstance(kind, RecordKind) else kind,
                ts=ts,
                prev_hash=prev_hash,
                payload=payload,
                producer=producer,
                version=version,
            )

            # Create record
            record = LedgerRecord(
                rid=rid,
                anchor_id=anchor_id,
                slot=slot,
                kind=kind,
                ts=ts,
                prev_hash=prev_hash,
                hash=record_hash,
                payload=payload,
                sig=sig,
                producer=producer,
                version=version,
            )

            # Store record
            self._records[rid] = record

            # Update anchor chain
            if anchor_id not in self._anchor_chains:
                self._anchor_chains[anchor_id] = []
            self._anchor_chains[anchor_id].append(rid)

            # Update metrics
            ledger_appends_total.labels(slot=slot, kind=kind.value, status="success").inc()
            ledger_records_total.set(len(self._records))

            self.logger.debug(
                f"Appended record {rid} for anchor {anchor_id} (kind={kind.value}, hash={record_hash[:8]}...)"
            )

            return record

    def get_chain(self, anchor_id: str) -> List[LedgerRecord]:
        """
        Get all records for an anchor in chronological order.

        Args:
            anchor_id: Truth anchor ID

        Returns:
            List of records ordered by timestamp
        """
        ledger_query_total.labels(query_type="chain", status="success").inc()
        rids = self._anchor_chains.get(anchor_id, [])
        records = [self._records[rid] for rid in rids]
        return sorted(records, key=lambda r: r.ts)

    def verify_chain(self, anchor_id: str) -> tuple[bool, List[str]]:
        """
        Verify hash chain continuity for an anchor.

        Args:
            anchor_id: Truth anchor ID

        Returns:
            (continuity_ok: bool, errors: List[str])
        """
        records = self.get_chain(anchor_id)
        if not records:
            return True, []

        errors = []

        for i, record in enumerate(records):
            # Verify record hash matches content
            is_valid = verify_record_hash(
                record_hash=record.hash,
                rid=record.rid,
                anchor_id=record.anchor_id,
                slot=record.slot,
                kind=record.kind.value if isinstance(record.kind, RecordKind) else record.kind,
                ts=record.ts,
                prev_hash=record.prev_hash,
                payload=record.payload,
                producer=record.producer,
                version=record.version,
            )

            if not is_valid:
                errors.append(f"Record {record.rid}: hash mismatch")

            # Verify continuity with previous record
            if i > 0:
                prev_record = records[i - 1]
                if record.prev_hash != prev_record.hash:
                    errors.append(
                        f"Record {record.rid}: prev_hash mismatch "
                        f"(expected {prev_record.hash[:8]}..., got {record.prev_hash[:8] if record.prev_hash else 'None'}...)"
                    )
                    ledger_continuity_breaks_total.labels(anchor_id=anchor_id).inc()
            else:
                # First record should have prev_hash=None
                if record.prev_hash is not None:
                    errors.append(f"Record {record.rid}: first record has non-null prev_hash")

        continuity_ok = len(errors) == 0
        return continuity_ok, errors

    def search(
        self,
        slot: Optional[str] = None,
        kind: Optional[RecordKind] = None,
        since: Optional[datetime] = None,
        limit: int = 100,
    ) -> List[LedgerRecord]:
        """
        Search ledger records by slot, kind, and time.

        Args:
            slot: Filter by slot ID
            kind: Filter by record kind
            since: Filter by timestamp (records after this time)
            limit: Maximum number of records to return

        Returns:
            List of matching records (most recent first)
        """
        ledger_query_total.labels(query_type="search", status="success").inc()
        records = list(self._records.values())

        # Apply filters
        if slot:
            records = [r for r in records if r.slot == slot]
        if kind:
            records = [r for r in records if r.kind == kind]
        if since:
            records = [r for r in records if r.ts >= since]

        # Sort by timestamp (most recent first) and limit
        records = sorted(records, key=lambda r: r.ts, reverse=True)[:limit]

        return records

    def create_checkpoint(
        self,
        range_start_rid: str,
        range_end_rid: str,
        sig: Optional[bytes] = None,
    ) -> Checkpoint:
        """
        Create a Merkle root checkpoint for a range of records.

        Args:
            range_start_rid: First record ID in range
            range_end_rid: Last record ID in range
            sig: Optional PQC signature over checkpoint

        Returns:
            Created Checkpoint
        """
        # Get all records in range (by timestamp order)
        all_records = sorted(self._records.values(), key=lambda r: r.ts)
        start_idx = next((i for i, r in enumerate(all_records) if r.rid == range_start_rid), None)
        end_idx = next((i for i, r in enumerate(all_records) if r.rid == range_end_rid), None)

        if start_idx is None or end_idx is None:
            raise ValueError(f"Invalid checkpoint range: {range_start_rid} to {range_end_rid}")

        range_records = all_records[start_idx : end_idx + 1]
        hashes = [r.hash for r in range_records]

        # Compute Merkle root
        merkle_root = compute_merkle_root(hashes)

        # Create checkpoint
        checkpoint = Checkpoint(
            cid=generate_checkpoint_id(),
            range_start=range_start_rid,
            range_end=range_end_rid,
            merkle_root=merkle_root,
            sig=sig,
            record_count=len(range_records),
        )

        self._checkpoints[checkpoint.cid] = checkpoint
        self.logger.info(
            f"Created checkpoint {checkpoint.cid}: {len(range_records)} records, root={merkle_root[:8]}..."
        )

        return checkpoint

    def get_checkpoint(self, cid: str) -> Optional[Checkpoint]:
        """Get checkpoint by ID."""
        return self._checkpoints.get(cid)

    def get_latest_checkpoint(self) -> Optional[Checkpoint]:
        """Get the most recent checkpoint."""
        if not self._checkpoints:
            return None
        return max(self._checkpoints.values(), key=lambda c: c.created_at)

    def _get_last_hash(self, anchor_id: str) -> Optional[str]:
        """Get the hash of the last record for an anchor."""
        rids = self._anchor_chains.get(anchor_id, [])
        if not rids:
            return None
        last_rid = rids[-1]
        return self._records[last_rid].hash

    async def span_for_checkpoint(self, anchor_id: str) -> Optional[Dict]:
        """
        Get span information for creating a checkpoint.

        Args:
            anchor_id: Anchor to get span for

        Returns:
            Dict with start_rid, end_rid, merkle_root, prev_root or None
        """
        records = self.get_chain(anchor_id)
        if not records:
            return None

        # Get record hashes
        from .canon import compute_record_hash
        hashes = []
        for record in records:
            # Recompute hash to ensure consistency
            h = compute_record_hash(
                rid=record.rid,
                anchor_id=record.anchor_id,
                slot=record.slot,
                kind=record.kind.value if hasattr(record.kind, 'value') else record.kind,
                ts=record.ts,
                prev_hash=record.prev_hash,
                payload=record.payload,
                producer=record.producer,
                version=record.version,
            )
            hashes.append(bytes.fromhex(h))

        # Compute Merkle root
        from .merkle import merkle_root
        root = merkle_root(hashes)

        # Get previous checkpoint root for chaining
        prev_root = None
        if hasattr(self, '_checkpoints') and self._checkpoints:
            # Find latest checkpoint for this anchor
            anchor_checkpoints = [cp for cp in self._checkpoints.values() if cp.get('anchor_id') == anchor_id]
            if anchor_checkpoints:
                latest_cp = max(anchor_checkpoints, key=lambda cp: cp.get('created_at', ''))
                prev_root = latest_cp.get('merkle_root')

        return {
            "start_rid": records[0].rid,
            "end_rid": records[-1].rid,
            "merkle_root": root.hex(),
            "prev_root": prev_root
        }

    async def persist_checkpoint(self, checkpoint) -> None:
        """
        Persist a checkpoint.

        Args:
            checkpoint: Checkpoint to persist
        """
        if hasattr(self, '_checkpoints'):
            cp_dict = checkpoint.to_dict() if hasattr(checkpoint, 'to_dict') else checkpoint
            self._checkpoints[cp_dict['id']] = cp_dict

    async def fetch_checkpoint(self, checkpoint_id: str):
        """
        Fetch a checkpoint by ID.

        Args:
            checkpoint_id: Checkpoint ID to fetch

        Returns:
            Checkpoint dict or None
        """
        if hasattr(self, '_checkpoints'):
            return self._checkpoints.get(checkpoint_id)
        return None

    async def query_hashes_between_rids(self, start_rid: str, end_rid: str) -> List[str]:
        """
        Query record hashes between record IDs.

        Args:
            start_rid: Starting record ID
            end_rid: Ending record ID

        Returns:
            List of hex hashes
        """
        # For in-memory store, find records in range
        # This is a simplified implementation
        all_records = []
        for anchor_records in self._anchor_chains.values():
            for rid in anchor_records:
                record = self._records.get(rid)
                if record:
                    all_records.append(record)

        # Sort by some ordering (simplified)
        all_records.sort(key=lambda r: r.ts)

        # Find range (simplified - assumes RIDs are sortable)
        start_idx = next((i for i, r in enumerate(all_records) if r.rid >= start_rid), 0)
        end_idx = next((i for i, r in enumerate(all_records) if r.rid > end_rid), len(all_records))

        range_records = all_records[start_idx:end_idx]

        # Return hashes
        from .canon import compute_record_hash
        hashes = []
        for record in range_records:
            h = compute_record_hash(
                rid=record.rid,
                anchor_id=record.anchor_id,
                slot=record.slot,
                kind=record.kind.value if hasattr(record.kind, 'value') else record.kind,
                ts=record.ts,
                prev_hash=record.prev_hash,
                payload=record.payload,
                producer=record.producer,
                version=record.version,
            )
            hashes.append(h)

        return hashes

    def get_stats(self) -> Dict:
        """Get ledger statistics."""
        return {
            "total_records": len(self._records),
            "total_anchors": len(self._anchor_chains),
            "total_checkpoints": len(getattr(self, '_checkpoints', {})),
        }
