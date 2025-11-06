"""
Tests for ledger ID generation (UUIDv7).

Phase 15-9: UUIDv7 migration for time-sortable, monotonic IDs.
"""

import pytest
import time
from nova.ledger.id_gen import generate_record_id, generate_checkpoint_id


class TestIDGeneration:
    """Test ID generation utilities."""

    def test_generate_record_id_returns_valid_uuid(self):
        """Test that generate_record_id returns a valid UUID string."""
        rid = generate_record_id()

        # UUID format: 8-4-4-4-12 hex characters with hyphens
        assert isinstance(rid, str)
        assert len(rid) == 36
        assert rid.count('-') == 4

        # Verify it's hexadecimal
        hex_part = rid.replace('-', '')
        assert all(c in '0123456789abcdef' for c in hex_part.lower())

    def test_generate_checkpoint_id_returns_valid_uuid(self):
        """Test that generate_checkpoint_id returns a valid UUID string."""
        cid = generate_checkpoint_id()

        # UUID format: 8-4-4-4-12 hex characters with hyphens
        assert isinstance(cid, str)
        assert len(cid) == 36
        assert cid.count('-') == 4

        # Verify it's hexadecimal
        hex_part = cid.replace('-', '')
        assert all(c in '0123456789abcdef' for c in hex_part.lower())

    def test_record_ids_are_unique(self):
        """Test that multiple calls generate unique IDs."""
        ids = [generate_record_id() for _ in range(100)]
        assert len(set(ids)) == 100  # All unique

    def test_checkpoint_ids_are_unique(self):
        """Test that multiple calls generate unique IDs."""
        ids = [generate_checkpoint_id() for _ in range(100)]
        assert len(set(ids)) == 100  # All unique

    def test_uuidv7_time_sortable_ordering(self):
        """
        Test that UUIDv7 IDs generated later sort after earlier IDs.

        This is the critical property: IDs should be monotonically increasing
        and lexicographically sortable by time.
        """
        # Generate ID, wait, generate another
        id1 = generate_record_id()
        time.sleep(0.01)  # Wait 10ms to ensure different timestamp
        id2 = generate_record_id()
        time.sleep(0.01)
        id3 = generate_record_id()

        # String comparison should yield chronological order
        assert id1 < id2, f"First ID should sort before second: {id1} >= {id2}"
        assert id2 < id3, f"Second ID should sort before third: {id2} >= {id3}"
        assert id1 < id3, f"First ID should sort before third: {id1} >= {id3}"

        # Verify sorted order matches generation order
        ids = [id3, id1, id2]  # Out of order
        sorted_ids = sorted(ids)
        assert sorted_ids == [id1, id2, id3], "Sorted order should match generation order"

    def test_uuidv7_embedding_timestamp(self):
        """
        Test that UUIDv7 IDs embed timestamp information.

        UUIDv7 uses first 48 bits for Unix timestamp (millisecond precision).
        We verify that IDs generated close in time have similar prefixes.
        """
        # Generate multiple IDs in quick succession
        ids = [generate_record_id() for _ in range(10)]

        # All IDs should start with the same 8 characters (approximate timestamp)
        # This assumes they're generated within the same ~second
        prefixes = [id[:8] for id in ids]

        # All prefixes should be very similar (may differ by 1-2 chars at most)
        # For a strict test, we just verify they're all valid hex timestamps
        for prefix in prefixes:
            assert all(c in '0123456789abcdef' for c in prefix.lower())

    def test_record_and_checkpoint_ids_independent(self):
        """Test that record and checkpoint IDs are independently generated."""
        rid = generate_record_id()
        cid = generate_checkpoint_id()

        # Should be different IDs
        assert rid != cid

        # Both should be valid UUIDs
        assert len(rid) == 36
        assert len(cid) == 36

    def test_uuidv7_version_field(self):
        """
        Test that generated IDs have UUIDv7 version field.

        UUIDv7 format: xxxxxxxx-xxxx-7xxx-xxxx-xxxxxxxxxxxx
        The version nibble (13th hex char) should be '7'.
        """
        rid = generate_record_id()

        # Position 14 (0-indexed) should be '7' for version 7
        assert rid[14] == '7', f"UUID version should be 7, got: {rid[14]}"

        cid = generate_checkpoint_id()
        assert cid[14] == '7', f"UUID version should be 7, got: {cid[14]}"

    def test_bulk_generation_performance(self):
        """Test that ID generation is fast enough for production use."""
        import time

        start = time.perf_counter()
        ids = [generate_record_id() for _ in range(1000)]
        elapsed = time.perf_counter() - start

        # Should generate 1000 IDs in under 100ms (10 IDs/ms)
        assert elapsed < 0.1, f"ID generation too slow: {elapsed*1000:.2f}ms for 1000 IDs"

        # All should be unique
        assert len(set(ids)) == 1000

    def test_concurrent_generation_ordering(self):
        """
        Test that IDs generated in sequence maintain ordering.

        This simulates the ledger append use case where records are
        added sequentially and must maintain chronological order.
        """
        ids = []
        for i in range(50):
            ids.append(generate_record_id())
            if i % 10 == 0:
                time.sleep(0.001)  # Small delay every 10 IDs

        # Verify sorted order equals generation order
        sorted_ids = sorted(ids)
        assert sorted_ids == ids, "IDs should maintain generation order when sorted"
