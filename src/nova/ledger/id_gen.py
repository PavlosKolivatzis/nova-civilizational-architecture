"""
ID generation utilities for ledger records and checkpoints.

Phase 15-9: UUIDv7 migration for time-sortable, monotonic IDs.
"""

from uuid6 import uuid7


def generate_record_id() -> str:
    """
    Generate a time-sortable record ID using UUIDv7.

    UUIDv7 provides:
    - Monotonic ordering: IDs generated later sort after earlier IDs
    - Timestamp embedding: First 48 bits are Unix timestamp (millisecond precision)
    - Lexicographic sortability: String comparison yields chronological order
    - Database-friendly: Better index performance than UUIDv4

    Returns:
        str: UUIDv7 formatted as lowercase hex string (e.g., "018c4c4a-1234-7abc-9def-0123456789ab")
    """
    return str(uuid7())


def generate_checkpoint_id() -> str:
    """
    Generate a time-sortable checkpoint ID using UUIDv7.

    Checkpoints use the same ID generation strategy as records for consistent
    time-based ordering across the ledger system.

    Returns:
        str: UUIDv7 formatted as lowercase hex string
    """
    return str(uuid7())
