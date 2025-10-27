"""
Tests for canonical JSON hashing and Merkle tree construction.

Phase 13: Autonomous Verification Ledger
"""

import pytest
from datetime import datetime, timezone
from nova.ledger.canon import (
    canonical_json,
    compute_hash,
    compute_record_hash,
    verify_record_hash,
    compute_merkle_root,
)


class TestCanonicalJSON:
    """Test canonical JSON serialization."""

    def test_canonical_json_deterministic(self):
        """Test that canonical JSON is deterministic."""
        data = {"b": 2, "a": 1, "c": 3}

        result1 = canonical_json(data)
        result2 = canonical_json(data)

        assert result1 == result2
        assert b'{"a":1,"b":2,"c":3}' == result1

    def test_canonical_json_sorts_keys(self):
        """Test that keys are sorted."""
        data = {"z": 1, "a": 2, "m": 3}
        result = canonical_json(data)

        assert result == b'{"a":2,"m":3,"z":1}'

    def test_canonical_json_datetime(self):
        """Test datetime serialization."""
        ts = datetime(2025, 10, 27, 12, 0, 0, tzinfo=timezone.utc)
        data = {"timestamp": ts}

        result = canonical_json(data)
        assert b'"timestamp":"2025-10-27T12:00:00+00:00"' in result

    def test_canonical_json_nested(self):
        """Test nested object serialization."""
        data = {
            "outer": {
                "z": 3,
                "a": 1,
            },
            "b": 2,
        }

        result = canonical_json(data)
        # Keys should be sorted at all levels
        assert b'{"b":2,"outer":{"a":1,"z":3}}' == result


class TestHashing:
    """Test SHA3-256 hashing."""

    def test_compute_hash_deterministic(self):
        """Test hash computation is deterministic."""
        data = b"test data"

        hash1 = compute_hash(data)
        hash2 = compute_hash(data)

        assert hash1 == hash2
        assert len(hash1) == 64  # SHA3-256 produces 64 hex chars

    def test_compute_hash_different_inputs(self):
        """Test different inputs produce different hashes."""
        hash1 = compute_hash(b"data1")
        hash2 = compute_hash(b"data2")

        assert hash1 != hash2

    def test_compute_hash_empty(self):
        """Test hashing empty data."""
        result = compute_hash(b"")
        assert len(result) == 64


class TestRecordHashing:
    """Test ledger record hashing."""

    def test_compute_record_hash_deterministic(self):
        """Test record hash is deterministic."""
        ts = datetime(2025, 10, 27, 12, 0, 0, tzinfo=timezone.utc)

        hash1 = compute_record_hash(
            rid="test-rid",
            anchor_id="anchor-1",
            slot="01",
            kind="ANCHOR_CREATED",
            ts=ts,
            prev_hash=None,
            payload={"test": "data"},
            producer="slot01",
            version="1.0.0",
        )

        hash2 = compute_record_hash(
            rid="test-rid",
            anchor_id="anchor-1",
            slot="01",
            kind="ANCHOR_CREATED",
            ts=ts,
            prev_hash=None,
            payload={"test": "data"},
            producer="slot01",
            version="1.0.0",
        )

        assert hash1 == hash2
        assert len(hash1) == 64

    def test_compute_record_hash_different_fields(self):
        """Test different fields produce different hashes."""
        ts = datetime(2025, 10, 27, 12, 0, 0, tzinfo=timezone.utc)

        hash1 = compute_record_hash(
            rid="rid-1",
            anchor_id="anchor-1",
            slot="01",
            kind="ANCHOR_CREATED",
            ts=ts,
            prev_hash=None,
            payload={"data": "a"},
            producer="slot01",
            version="1.0.0",
        )

        hash2 = compute_record_hash(
            rid="rid-1",
            anchor_id="anchor-1",
            slot="01",
            kind="ANCHOR_CREATED",
            ts=ts,
            prev_hash=None,
            payload={"data": "b"},  # Different payload
            producer="slot01",
            version="1.0.0",
        )

        assert hash1 != hash2

    def test_verify_record_hash_valid(self):
        """Test verifying a valid record hash."""
        ts = datetime(2025, 10, 27, 12, 0, 0, tzinfo=timezone.utc)

        record_hash = compute_record_hash(
            rid="test-rid",
            anchor_id="anchor-1",
            slot="01",
            kind="PQC_SIGNED",
            ts=ts,
            prev_hash="prev123",
            payload={"sig": "abc"},
            producer="slot01",
            version="1.0.0",
        )

        is_valid = verify_record_hash(
            record_hash=record_hash,
            rid="test-rid",
            anchor_id="anchor-1",
            slot="01",
            kind="PQC_SIGNED",
            ts=ts,
            prev_hash="prev123",
            payload={"sig": "abc"},
            producer="slot01",
            version="1.0.0",
        )

        assert is_valid is True

    def test_verify_record_hash_invalid(self):
        """Test verifying an invalid record hash."""
        ts = datetime(2025, 10, 27, 12, 0, 0, tzinfo=timezone.utc)

        is_valid = verify_record_hash(
            record_hash="invalid_hash",
            rid="test-rid",
            anchor_id="anchor-1",
            slot="01",
            kind="PQC_SIGNED",
            ts=ts,
            prev_hash=None,
            payload={"sig": "abc"},
            producer="slot01",
            version="1.0.0",
        )

        assert is_valid is False


class TestMerkleTree:
    """Test Merkle tree construction."""

    def test_merkle_root_empty(self):
        """Test Merkle root of empty list."""
        root = compute_merkle_root([])
        assert len(root) == 64  # Valid hash

    def test_merkle_root_single(self):
        """Test Merkle root of single hash."""
        single_hash = compute_hash(b"test")
        root = compute_merkle_root([single_hash])

        assert root == single_hash

    def test_merkle_root_multiple(self):
        """Test Merkle root of multiple hashes."""
        hashes = [
            compute_hash(b"hash1"),
            compute_hash(b"hash2"),
            compute_hash(b"hash3"),
            compute_hash(b"hash4"),
        ]

        root = compute_merkle_root(hashes)
        assert len(root) == 64
        assert root not in hashes  # Root should be different from leaf hashes

    def test_merkle_root_deterministic(self):
        """Test Merkle root is deterministic."""
        hashes = [compute_hash(b"a"), compute_hash(b"b"), compute_hash(b"c")]

        root1 = compute_merkle_root(hashes)
        root2 = compute_merkle_root(hashes)

        assert root1 == root2

    def test_merkle_root_order_matters(self):
        """Test that hash order affects Merkle root."""
        hashes_a = [compute_hash(b"1"), compute_hash(b"2")]
        hashes_b = [compute_hash(b"2"), compute_hash(b"1")]

        root_a = compute_merkle_root(hashes_a)
        root_b = compute_merkle_root(hashes_b)

        assert root_a != root_b
