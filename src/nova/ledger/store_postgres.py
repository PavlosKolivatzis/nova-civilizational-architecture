"""
PostgreSQL-backed ledger store with async SQLAlchemy 2.x.

Phase 14-1: Durable persistence for Autonomous Verification Ledger.
"""

from __future__ import annotations

import logging
import time
from typing import Dict, List, Optional

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy import text

from .model import LedgerRecord, RecordKind, Checkpoint
from .canon import compute_record_hash, verify_record_hash, compute_merkle_root
from .id_gen import generate_record_id, generate_checkpoint_id
from .metrics import (
    ledger_appends_total,
    ledger_append_duration_seconds,
    ledger_query_total,
    ledger_continuity_breaks_total,
    ledger_records_total,
    ledger_persist_latency_ms,
    ledger_persist_errors_total,
    ledger_backend_up,
    ledger_persist_fallback_total,
)
from prometheus_client import Summary, Counter, Gauge


class PostgresLedgerStore:
    """
    PostgreSQL-backed ledger store with async operations.

    Maintains full compatibility with LedgerStore interface while providing
    durable persistence and horizontal scalability.
    """

    def __init__(
        self,
        dsn: str,
        pool_size: int = 5,
        timeout: int = 30,
        logger: Optional[logging.Logger] = None
    ):
        """Initialize PostgreSQL ledger store."""
        self.logger = logger or logging.getLogger("ledger.store.postgres")
        self.dsn = dsn
        self.pool_size = pool_size
        self.timeout = timeout

        # Initialize async engine
        self.engine = create_async_engine(
            dsn,
            pool_size=pool_size,
            pool_timeout=timeout,
            echo=False  # Disable SQL logging in production
        )
        self.Session = async_sessionmaker(self.engine, expire_on_commit=False)

        # Health check
        self._last_health_check = 0
        self._health_check_interval = 60  # seconds

    async def append(
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
        Append a new record to the PostgreSQL ledger with continuity enforcement.

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
            Exception: On database errors (will fallback to memory store)
        """
        start_time = time.perf_counter()

        try:
            # Generate record ID (UUIDv7 for time-sortable ordering)
            rid = generate_record_id()
            ts = time.time()  # Use float timestamp for SQL

            # Get previous record hash for this anchor
            prev_hash = await self._get_last_hash(anchor_id)

            # Compute record hash
            record_hash = compute_record_hash(
                rid=rid,
                anchor_id=anchor_id,
                slot=slot,
                kind=kind.value if isinstance(kind, RecordKind) else kind,
                ts=ts,  # Pass as float, will be converted in canon.py
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
                ts=ts,  # This will be converted to datetime in model
                prev_hash=prev_hash,
                hash=record_hash,
                payload=payload,
                sig=sig,
                producer=producer,
                version=version,
            )

            # Persist to database
            await self._persist_record(record)

            # Update metrics
            ledger_appends_total.labels(slot=slot, kind=kind.value, status="success").inc()
            ledger_records_total.set(await self._count_records())
            ledger_backend_up.set(1)

            latency_ms = (time.perf_counter() - start_time) * 1000
            ledger_persist_latency_ms.labels(operation="append").observe(latency_ms)

            self.logger.debug(
                f"Appended record {rid} for anchor {anchor_id} (kind={kind.value}, hash={record_hash[:8]}...)"
            )

            return record

        except Exception as e:
            ledger_persist_errors_total.labels(operation="append").inc()
            ledger_backend_up.set(0)
            self.logger.error(f"Failed to append record: {e}")
            raise

    async def get_chain(self, anchor_id: str) -> List[LedgerRecord]:
        """
        Get all records for an anchor in chronological order.

        Args:
            anchor_id: Truth anchor ID

        Returns:
            List of records ordered by timestamp
        """
        try:
            async with self.Session() as session:
                result = await session.execute(
                    text("""
                        SELECT rid, anchor_id, slot, kind, ts, prev_hash, hash,
                               payload, sig, producer, version
                        FROM ledger_records
                        WHERE anchor_id = :anchor_id
                        ORDER BY ts ASC
                    """),
                    {"anchor_id": anchor_id}
                )
                rows = result.mappings().all()

                records = []
                for row in rows:
                    # Convert back to LedgerRecord
                    record = LedgerRecord(
                        rid=str(row["rid"]),
                        anchor_id=str(row["anchor_id"]),
                        slot=row["slot"],
                        kind=RecordKind(row["kind"]),
                        ts=row["ts"],  # Already datetime
                        prev_hash=row["prev_hash"],
                        hash=row["hash"],
                        payload=row["payload"],
                        sig=row["sig"],
                        producer=row["producer"] or "unknown",
                        version=row["version"] or "unknown",
                    )
                    records.append(record)

                ledger_query_total.labels(query_type="chain", status="success").inc()
                return records

        except Exception as e:
            ledger_persist_errors_total.labels(operation="query_chain").inc()
            ledger_backend_up.set(0)
            self.logger.error(f"Failed to query chain for {anchor_id}: {e}")
            raise

    async def verify_chain(self, anchor_id: str) -> tuple[bool, List[str]]:
        """
        Verify hash chain continuity for an anchor.

        Args:
            anchor_id: Truth anchor ID

        Returns:
            (continuity_ok: bool, errors: List[str])
        """
        records = await self.get_chain(anchor_id)
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

    async def search(
        self,
        slot: Optional[str] = None,
        kind: Optional[RecordKind] = None,
        since: Optional[float] = None,
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
        try:
            conditions = []
            params = {}

            if slot:
                conditions.append("slot = :slot")
                params["slot"] = slot
            if kind:
                conditions.append("kind = :kind")
                params["kind"] = kind.value
            if since:
                conditions.append("ts >= :since")
                params["since"] = since

            where_clause = " AND ".join(conditions) if conditions else "TRUE"

            async with self.Session() as session:
                result = await session.execute(
                    text(f"""
                        SELECT rid, anchor_id, slot, kind, ts, prev_hash, hash,
                               payload, sig, producer, version
                        FROM ledger_records
                        WHERE {where_clause}
                        ORDER BY ts DESC
                        LIMIT :limit
                    """),
                    {**params, "limit": limit}
                )
                rows = result.mappings().all()

                records = []
                for row in rows:
                    record = LedgerRecord(
                        rid=str(row["rid"]),
                        anchor_id=str(row["anchor_id"]),
                        slot=row["slot"],
                        kind=RecordKind(row["kind"]),
                        ts=row["ts"],
                        prev_hash=row["prev_hash"],
                        hash=row["hash"],
                        payload=row["payload"],
                        sig=row["sig"],
                        producer=row["producer"] or "unknown",
                        version=row["version"] or "unknown",
                    )
                    records.append(record)

                ledger_query_total.labels(query_type="search", status="success").inc()
                return records

        except Exception as e:
            ledger_persist_errors_total.labels(operation="search").inc()
            ledger_backend_up.set(0)
            self.logger.error(f"Failed to search records: {e}")
            raise

    async def create_checkpoint(
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
        async with self.Session() as session:
            result = await session.execute(
                text("""
                    SELECT hash FROM ledger_records
                    WHERE ts >= (SELECT ts FROM ledger_records WHERE rid = :start_rid)
                    AND ts <= (SELECT ts FROM ledger_records WHERE rid = :end_rid)
                    ORDER BY ts ASC
                """),
                {"start_rid": range_start_rid, "end_rid": range_end_rid}
            )
            hashes = [row[0] for row in result.fetchall()]

        if not hashes:
            raise ValueError(f"No records found in range {range_start_rid} to {range_end_rid}")

        # Compute Merkle root
        merkle_root = compute_merkle_root(hashes)

        # Create checkpoint
        checkpoint = Checkpoint(
            cid=generate_checkpoint_id(),
            range_start=range_start_rid,
            range_end=range_end_rid,
            merkle_root=merkle_root,
            sig=sig,
            record_count=len(hashes),
        )

        # Persist checkpoint
        await self._persist_checkpoint(checkpoint)

        self.logger.info(
            f"Created checkpoint {checkpoint.cid}: {len(hashes)} records, root={merkle_root[:8]}..."
        )

        return checkpoint

    async def get_checkpoint(self, cid: str) -> Optional[Checkpoint]:
        """Get checkpoint by ID."""
        try:
            async with self.Session() as session:
                result = await session.execute(
                    text("""
                        SELECT cid, range_start, range_end, merkle_root, sig, created_at, record_count
                        FROM ledger_checkpoints
                        WHERE cid = :cid
                    """),
                    {"cid": cid}
                )
                row = result.mappings().first()

                if row:
                    return Checkpoint(
                        cid=str(row["cid"]),
                        range_start=row["range_start"],
                        range_end=row["range_end"],
                        merkle_root=row["merkle_root"],
                        sig=row["sig"],
                        created_at=row["created_at"],
                        record_count=row["record_count"],
                    )
                return None

        except Exception as e:
            ledger_persist_errors_total.labels(operation="get_checkpoint").inc()
            self.logger.error(f"Failed to get checkpoint {cid}: {e}")
            raise

    async def get_latest_checkpoint(self) -> Optional[Checkpoint]:
        """Get the most recent checkpoint."""
        try:
            async with self.Session() as session:
                result = await session.execute(
                    text("""
                        SELECT cid, range_start, range_end, merkle_root, sig, created_at, record_count
                        FROM ledger_checkpoints
                        ORDER BY created_at DESC
                        LIMIT 1
                    """)
                )
                row = result.mappings().first()

                if row:
                    return Checkpoint(
                        cid=str(row["cid"]),
                        range_start=row["range_start"],
                        range_end=row["range_end"],
                        merkle_root=row["merkle_root"],
                        sig=row["sig"],
                        created_at=row["created_at"],
                        record_count=row["record_count"],
                    )
                return None

        except Exception as e:
            ledger_persist_errors_total.labels(operation="get_latest_checkpoint").inc()
            self.logger.error(f"Failed to get latest checkpoint: {e}")
            raise

    async def get_stats(self) -> Dict:
        """Get ledger statistics."""
        try:
            async with self.Session() as session:
                # Count total records
                result = await session.execute(text("SELECT COUNT(*) FROM ledger_records"))
                total_records = result.scalar()

                # Count unique anchors
                result = await session.execute(text("SELECT COUNT(DISTINCT anchor_id) FROM ledger_records"))
                total_anchors = result.scalar()

                # Count checkpoints
                result = await session.execute(text("SELECT COUNT(*) FROM ledger_checkpoints"))
                total_checkpoints = result.scalar()

                return {
                    "total_records": total_records or 0,
                    "total_anchors": total_anchors or 0,
                    "total_checkpoints": total_checkpoints or 0,
                }

        except Exception as e:
            ledger_persist_errors_total.labels(operation="get_stats").inc()
            self.logger.error(f"Failed to get stats: {e}")
            raise

    async def _persist_record(self, record: LedgerRecord) -> None:
        """Persist a single record to PostgreSQL."""
        async with self.Session() as session:
            await session.execute(
                text("""
                    INSERT INTO ledger_records
                    (rid, anchor_id, slot, kind, ts, prev_hash, hash, payload, sig, producer, version)
                    VALUES (:rid, :anchor_id, :slot, :kind, :ts, :prev_hash, :hash, :payload, :sig, :producer, :version)
                    ON CONFLICT (hash) DO NOTHING
                """),
                {
                    "rid": record.rid,
                    "anchor_id": record.anchor_id,
                    "slot": record.slot,
                    "kind": record.kind.value,
                    "ts": record.ts,
                    "prev_hash": record.prev_hash,
                    "hash": record.hash,
                    "payload": record.payload,
                    "sig": record.sig,
                    "producer": record.producer,
                    "version": record.version,
                }
            )
            await session.commit()

    async def _persist_checkpoint(self, checkpoint: Checkpoint) -> None:
        """Persist a checkpoint to PostgreSQL."""
        async with self.Session() as session:
            await session.execute(
                text("""
                    INSERT INTO ledger_checkpoints
                    (cid, range_start, range_end, merkle_root, sig, record_count)
                    VALUES (:cid, :range_start, :range_end, :merkle_root, :sig, :record_count)
                """),
                {
                    "cid": checkpoint.cid,
                    "range_start": checkpoint.range_start,
                    "range_end": checkpoint.range_end,
                    "merkle_root": checkpoint.merkkle_root,
                    "sig": checkpoint.sig,
                    "record_count": checkpoint.record_count,
                }
            )
            await session.commit()

    async def _get_last_hash(self, anchor_id: str) -> Optional[str]:
        """Get the hash of the last record for an anchor."""
        try:
            async with self.Session() as session:
                result = await session.execute(
                    text("""
                        SELECT hash FROM ledger_records
                        WHERE anchor_id = :anchor_id
                        ORDER BY ts DESC
                        LIMIT 1
                    """),
                    {"anchor_id": anchor_id}
                )
                row = result.first()
                return row[0] if row else None

        except Exception as e:
            ledger_persist_errors_total.labels(operation="_get_last_hash").inc()
            self.logger.error(f"Failed to get last hash for {anchor_id}: {e}")
            raise

    async def span_for_checkpoint(self, anchor_id: str) -> Optional[Dict]:
        """
        Get span information for creating a checkpoint.

        Args:
            anchor_id: Anchor to get span for

        Returns:
            Dict with start_rid, end_rid, merkle_root, prev_root or None
        """
        try:
            async with self.Session() as session:
                # Get all records for anchor ordered by timestamp
                result = await session.execute(
                    text("""
                        SELECT rid, hash FROM ledger_records
                        WHERE anchor_id = :anchor_id
                        ORDER BY ts ASC
                    """),
                    {"anchor_id": anchor_id}
                )
                rows = result.fetchall()

                if not rows:
                    return None

                # Extract hashes and RIDs
                rids = [row[0] for row in rows]
                hashes_hex = [row[1] for row in rows]

                # Convert to bytes and compute Merkle root
                digests = [bytes.fromhex(h) for h in hashes_hex]
                from .merkle import merkle_root
                root = merkle_root(digests)

                # Get previous checkpoint root for chaining
                prev_result = await session.execute(
                    text("""
                        SELECT merkle_root FROM ledger_checkpoints
                        WHERE anchor_id = :anchor_id
                        ORDER BY ts DESC
                        LIMIT 1
                    """),
                    {"anchor_id": anchor_id}
                )
                prev_row = prev_result.first()
                prev_root = prev_row[0] if prev_row else None

                return {
                    "start_rid": str(rids[0]),
                    "end_rid": str(rids[-1]),
                    "merkle_root": root.hex(),
                    "prev_root": prev_root
                }

        except Exception as e:
            ledger_persist_errors_total.labels(operation="span_for_checkpoint").inc()
            self.logger.error(f"Failed to get span for checkpoint: {e}")
            raise

    async def persist_checkpoint(self, checkpoint) -> None:
        """
        Persist a checkpoint.

        Args:
            checkpoint: Checkpoint to persist
        """
        try:
            async with self.Session() as session:
                cp_dict = checkpoint.to_dict() if hasattr(checkpoint, 'to_dict') else checkpoint
                await session.execute(
                    text("""
                        INSERT INTO ledger_checkpoints
                        (id, anchor_id, merkle_root, start_rid, end_rid, prev_root, ts, sig, key_id, version)
                        VALUES (:id, :anchor_id, :merkle_root, :start_rid, :end_rid, :prev_root, :ts, :sig, :key_id, :version)
                    """),
                    {
                        "id": cp_dict["id"],
                        "anchor_id": cp_dict["anchor_id"],
                        "merkle_root": cp_dict["merkle_root"],
                        "start_rid": cp_dict["start_rid"],
                        "end_rid": cp_dict["end_rid"],
                        "prev_root": cp_dict.get("prev_root"),
                        "ts": cp_dict["ts"],
                        "sig": cp_dict.get("sig"),
                        "key_id": cp_dict.get("key_id"),
                        "version": cp_dict.get("version", "cp-v1")
                    }
                )
                await session.commit()

        except Exception as e:
            ledger_persist_errors_total.labels(operation="persist_checkpoint").inc()
            self.logger.error(f"Failed to persist checkpoint: {e}")
            raise

    async def fetch_checkpoint(self, checkpoint_id: str):
        """
        Fetch a checkpoint by ID.

        Args:
            checkpoint_id: Checkpoint ID to fetch

        Returns:
            Checkpoint dict or None
        """
        try:
            async with self.Session() as session:
                result = await session.execute(
                    text("""
                        SELECT id, anchor_id, merkle_root, start_rid, end_rid, prev_root, ts, sig, key_id, version
                        FROM ledger_checkpoints
                        WHERE id = :id
                    """),
                    {"id": checkpoint_id}
                )
                row = result.first()

                if row:
                    from .checkpoint_types import Checkpoint
                    sig = bytes.fromhex(row[7]) if row[7] else None
                    return Checkpoint(
                        id=str(row[0]),
                        anchor_id=str(row[1]),
                        merkle_root=row[2],
                        start_rid=str(row[3]),
                        end_rid=str(row[4]),
                        prev_root=row[5],
                        ts=row[6],
                        sig=sig,
                        key_id=row[8],
                        version=row[9] or "cp-v1"
                    )
                return None

        except Exception as e:
            ledger_persist_errors_total.labels(operation="fetch_checkpoint").inc()
            self.logger.error(f"Failed to fetch checkpoint {checkpoint_id}: {e}")
            raise

    async def query_hashes_between_rids(self, start_rid: str, end_rid: str) -> List[str]:
        """
        Query record hashes between record IDs.

        Args:
            start_rid: Starting record ID
            end_rid: Ending record ID

        Returns:
            List of hex hashes
        """
        try:
            async with self.Session() as session:
                # Get records in RID range (simplified - assumes RIDs are UUIDs)
                result = await session.execute(
                    text("""
                        SELECT hash FROM ledger_records
                        WHERE rid >= :start_rid AND rid <= :end_rid
                        ORDER BY rid ASC
                    """),
                    {"start_rid": start_rid, "end_rid": end_rid}
                )
                rows = result.fetchall()
                return [row[0] for row in rows]

        except Exception as e:
            ledger_persist_errors_total.labels(operation="query_hashes_between_rids").inc()
            self.logger.error(f"Failed to query hashes between RIDs: {e}")
            raise

    async def _count_records(self) -> int:
        """Count total records in the ledger."""
        try:
            async with self.Session() as session:
                result = await session.execute(text("SELECT COUNT(*) FROM ledger_records"))
                return result.scalar() or 0

        except Exception as e:
            ledger_persist_errors_total.labels(operation="_count_records").inc()
            self.logger.error(f"Failed to count records: {e}")
            raise
