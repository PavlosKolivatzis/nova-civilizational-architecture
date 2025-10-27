"""
Tests for ledger store (append, query, continuity verification).

Phase 13: Autonomous Verification Ledger
"""

import pytest
from datetime import datetime, timedelta, timezone
from nova.ledger.store import LedgerStore, ContinuityError
from nova.ledger.model import RecordKind


class TestLedgerStore:
    """Test ledger store operations."""

    def test_append_creates_record(self):
        """Test appending a record creates it successfully."""
        store = LedgerStore()

        record = store.append(
            anchor_id="anchor-1",
            slot="01",
            kind=RecordKind.ANCHOR_CREATED,
            payload={"entropy": "abc123"},
            producer="slot01",
            version="1.0.0",
        )

        assert record.rid is not None
        assert record.anchor_id == "anchor-1"
        assert record.slot == "01"
        assert record.kind == RecordKind.ANCHOR_CREATED
        assert record.prev_hash is None  # First record
        assert record.hash is not None
        assert len(record.hash) == 64  # SHA3-256

    def test_append_chain_creates_prev_hash(self):
        """Test appending multiple records creates hash chain."""
        store = LedgerStore()

        record1 = store.append(
            anchor_id="anchor-1",
            slot="01",
            kind=RecordKind.ANCHOR_CREATED,
            payload={"step": 1},
        )

        record2 = store.append(
            anchor_id="anchor-1",
            slot="01",
            kind=RecordKind.PQC_SIGNED,
            payload={"step": 2},
        )

        assert record1.prev_hash is None
        assert record2.prev_hash == record1.hash

    def test_get_chain_returns_ordered_records(self):
        """Test getting chain returns records in order."""
        store = LedgerStore()

        # Append 3 records
        store.append(
            anchor_id="anchor-1",
            slot="01",
            kind=RecordKind.ANCHOR_CREATED,
            payload={"seq": 1},
        )
        store.append(
            anchor_id="anchor-1",
            slot="02",
            kind=RecordKind.DELTATHRESH_APPLIED,
            payload={"seq": 2},
        )
        store.append(
            anchor_id="anchor-1",
            slot="08",
            kind=RecordKind.PQC_VERIFIED,
            payload={"seq": 3},
        )

        chain = store.get_chain("anchor-1")
        assert len(chain) == 3
        assert chain[0].payload["seq"] == 1
        assert chain[1].payload["seq"] == 2
        assert chain[2].payload["seq"] == 3

    def test_verify_chain_valid(self):
        """Test verifying a valid hash chain."""
        store = LedgerStore()

        store.append(anchor_id="anchor-1", slot="01", kind=RecordKind.ANCHOR_CREATED, payload={})
        store.append(anchor_id="anchor-1", slot="01", kind=RecordKind.PQC_SIGNED, payload={})
        store.append(anchor_id="anchor-1", slot="08", kind=RecordKind.PQC_VERIFIED, payload={})

        continuity_ok, errors = store.verify_chain("anchor-1")
        assert continuity_ok is True
        assert len(errors) == 0

    def test_verify_chain_detects_tampering(self):
        """Test that tampering with a record breaks verification."""
        store = LedgerStore()

        record1 = store.append(
            anchor_id="anchor-1", slot="01", kind=RecordKind.ANCHOR_CREATED, payload={"data": "original"}
        )
        record2 = store.append(anchor_id="anchor-1", slot="01", kind=RecordKind.PQC_SIGNED, payload={})

        # Tamper with record1's payload (simulate attack)
        record1.payload["data"] = "tampered"

        continuity_ok, errors = store.verify_chain("anchor-1")
        assert continuity_ok is False
        assert len(errors) > 0
        assert "hash mismatch" in errors[0].lower()

    def test_search_by_slot(self):
        """Test searching records by slot."""
        store = LedgerStore()

        store.append(anchor_id="a1", slot="01", kind=RecordKind.ANCHOR_CREATED, payload={})
        store.append(anchor_id="a2", slot="02", kind=RecordKind.DELTATHRESH_APPLIED, payload={})
        store.append(anchor_id="a3", slot="01", kind=RecordKind.PQC_SIGNED, payload={})

        results = store.search(slot="01")
        assert len(results) == 2
        assert all(r.slot == "01" for r in results)

    def test_search_by_kind(self):
        """Test searching records by kind."""
        store = LedgerStore()

        store.append(anchor_id="a1", slot="01", kind=RecordKind.ANCHOR_CREATED, payload={})
        store.append(anchor_id="a2", slot="01", kind=RecordKind.PQC_SIGNED, payload={})
        store.append(anchor_id="a3", slot="02", kind=RecordKind.DELTATHRESH_APPLIED, payload={})

        results = store.search(kind=RecordKind.PQC_SIGNED)
        assert len(results) == 1
        assert results[0].kind == RecordKind.PQC_SIGNED

    def test_search_by_time(self):
        """Test searching records by timestamp."""
        store = LedgerStore()

        now = datetime.now(timezone.utc)
        cutoff = now + timedelta(seconds=1)

        store.append(anchor_id="a1", slot="01", kind=RecordKind.ANCHOR_CREATED, payload={})

        # This record should be after cutoff
        import time

        time.sleep(1.5)
        store.append(anchor_id="a2", slot="01", kind=RecordKind.PQC_SIGNED, payload={})

        results = store.search(since=cutoff)
        assert len(results) == 1
        assert results[0].anchor_id == "a2"

    def test_search_limit(self):
        """Test search respects limit parameter."""
        store = LedgerStore()

        for i in range(10):
            store.append(anchor_id=f"a{i}", slot="01", kind=RecordKind.ANCHOR_CREATED, payload={})

        results = store.search(limit=5)
        assert len(results) == 5

    def test_create_checkpoint(self):
        """Test creating a Merkle checkpoint."""
        store = LedgerStore()

        r1 = store.append(anchor_id="a1", slot="01", kind=RecordKind.ANCHOR_CREATED, payload={})
        r2 = store.append(anchor_id="a2", slot="01", kind=RecordKind.PQC_SIGNED, payload={})
        r3 = store.append(anchor_id="a3", slot="02", kind=RecordKind.DELTATHRESH_APPLIED, payload={})

        checkpoint = store.create_checkpoint(
            range_start_rid=r1.rid,
            range_end_rid=r3.rid,
        )

        assert checkpoint.cid is not None
        assert checkpoint.range_start == r1.rid
        assert checkpoint.range_end == r3.rid
        assert checkpoint.merkle_root is not None
        assert len(checkpoint.merkle_root) == 64  # SHA3-256
        assert checkpoint.record_count == 3

    def test_get_checkpoint(self):
        """Test retrieving a checkpoint."""
        store = LedgerStore()

        r1 = store.append(anchor_id="a1", slot="01", kind=RecordKind.ANCHOR_CREATED, payload={})
        r2 = store.append(anchor_id="a2", slot="01", kind=RecordKind.PQC_SIGNED, payload={})

        checkpoint = store.create_checkpoint(range_start_rid=r1.rid, range_end_rid=r2.rid)

        retrieved = store.get_checkpoint(checkpoint.cid)
        assert retrieved is not None
        assert retrieved.cid == checkpoint.cid
        assert retrieved.merkle_root == checkpoint.merkle_root

    def test_get_latest_checkpoint(self):
        """Test getting the most recent checkpoint."""
        store = LedgerStore()

        r1 = store.append(anchor_id="a1", slot="01", kind=RecordKind.ANCHOR_CREATED, payload={})
        r2 = store.append(anchor_id="a2", slot="01", kind=RecordKind.PQC_SIGNED, payload={})
        r3 = store.append(anchor_id="a3", slot="02", kind=RecordKind.DELTATHRESH_APPLIED, payload={})

        cp1 = store.create_checkpoint(range_start_rid=r1.rid, range_end_rid=r2.rid)
        import time

        time.sleep(0.1)
        cp2 = store.create_checkpoint(range_start_rid=r2.rid, range_end_rid=r3.rid)

        latest = store.get_latest_checkpoint()
        assert latest is not None
        assert latest.cid == cp2.cid

    def test_get_stats(self):
        """Test getting ledger statistics."""
        store = LedgerStore()

        store.append(anchor_id="a1", slot="01", kind=RecordKind.ANCHOR_CREATED, payload={})
        store.append(anchor_id="a1", slot="01", kind=RecordKind.PQC_SIGNED, payload={})
        store.append(anchor_id="a2", slot="02", kind=RecordKind.DELTATHRESH_APPLIED, payload={})

        stats = store.get_stats()
        assert stats["total_records"] == 3
        assert stats["total_anchors"] == 2
        assert stats["total_checkpoints"] == 0

    def test_multiple_anchor_chains_independent(self):
        """Test that different anchors maintain independent chains."""
        store = LedgerStore()

        # Anchor 1 chain
        a1_r1 = store.append(anchor_id="anchor-1", slot="01", kind=RecordKind.ANCHOR_CREATED, payload={})
        a1_r2 = store.append(anchor_id="anchor-1", slot="01", kind=RecordKind.PQC_SIGNED, payload={})

        # Anchor 2 chain
        a2_r1 = store.append(anchor_id="anchor-2", slot="01", kind=RecordKind.ANCHOR_CREATED, payload={})
        a2_r2 = store.append(anchor_id="anchor-2", slot="08", kind=RecordKind.PQC_VERIFIED, payload={})

        # Verify chains are independent
        chain1 = store.get_chain("anchor-1")
        chain2 = store.get_chain("anchor-2")

        assert len(chain1) == 2
        assert len(chain2) == 2
        assert chain1[0].rid == a1_r1.rid
        assert chain2[0].rid == a2_r1.rid
        assert a1_r2.prev_hash == a1_r1.hash
        assert a2_r2.prev_hash == a2_r1.hash
