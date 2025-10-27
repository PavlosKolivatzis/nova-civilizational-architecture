"""
Canonical hashing for ledger records.

Provides deterministic JSON serialization and SHA3-256 hashing for
tamper-evident record chains.

Phase 13: Autonomous Verification Ledger
"""

from __future__ import annotations

import hashlib
import json
from typing import Dict, Any, Optional
from datetime import datetime


def canonical_json(obj: Dict[str, Any]) -> bytes:
    """
    Serialize object to canonical JSON bytes.

    Uses sorted keys, no whitespace, UTF-8 encoding for deterministic hashing.

    Args:
        obj: Dictionary to serialize

    Returns:
        UTF-8 encoded JSON bytes
    """
    return json.dumps(
        obj,
        sort_keys=True,
        separators=(',', ':'),
        ensure_ascii=False,
        default=_json_serializer,
    ).encode('utf-8')


def _json_serializer(obj: Any) -> Any:
    """Custom JSON serializer for datetime and other types."""
    if isinstance(obj, datetime):
        return obj.isoformat()
    raise TypeError(f"Object of type {type(obj).__name__} is not JSON serializable")


def compute_hash(data: bytes) -> str:
    """
    Compute SHA3-256 hash of data.

    Args:
        data: Bytes to hash

    Returns:
        Hex-encoded hash string
    """
    return hashlib.sha3_256(data).hexdigest()


def compute_record_hash(
    rid: str,
    anchor_id: str,
    slot: str,
    kind: str,
    ts: datetime,
    prev_hash: Optional[str],
    payload: Dict[str, Any],
    producer: str,
    version: str,
) -> str:
    """
    Compute canonical hash for a ledger record.

    Creates a canonical representation of the record fields and hashes
    with SHA3-256. The hash covers all immutable fields including prev_hash.

    Args:
        rid: Record UUID
        anchor_id: Truth anchor ID
        slot: Slot identifier
        kind: Record kind (event type)
        ts: Timestamp
        prev_hash: Previous record hash (None for first record)
        payload: Event-specific data
        producer: Service that created the record
        version: Software version

    Returns:
        Hex-encoded SHA3-256 hash
    """
    canonical = {
        "rid": rid,
        "anchor_id": anchor_id,
        "slot": slot,
        "kind": kind,
        "ts": ts.isoformat(),
        "prev_hash": prev_hash,
        "payload": payload,
        "producer": producer,
        "version": version,
    }

    canonical_bytes = canonical_json(canonical)
    return compute_hash(canonical_bytes)


def verify_record_hash(
    record_hash: str,
    rid: str,
    anchor_id: str,
    slot: str,
    kind: str,
    ts: datetime,
    prev_hash: Optional[str],
    payload: Dict[str, Any],
    producer: str,
    version: str,
) -> bool:
    """
    Verify that a record's hash matches its content.

    Args:
        record_hash: Hash to verify
        (remaining args): Record fields

    Returns:
        True if hash matches, False otherwise
    """
    computed = compute_record_hash(
        rid=rid,
        anchor_id=anchor_id,
        slot=slot,
        kind=kind,
        ts=ts,
        prev_hash=prev_hash,
        payload=payload,
        producer=producer,
        version=version,
    )
    return computed == record_hash


def compute_merkle_root(hashes: list[str]) -> str:
    """
    Compute Merkle root from a list of record hashes.

    Uses simple binary tree construction with SHA3-256.

    Args:
        hashes: List of hex-encoded record hashes

    Returns:
        Hex-encoded Merkle root hash
    """
    if not hashes:
        return compute_hash(b"")

    if len(hashes) == 1:
        return hashes[0]

    # Build tree bottom-up
    current_level = hashes[:]

    while len(current_level) > 1:
        next_level = []

        for i in range(0, len(current_level), 2):
            left = current_level[i]

            # If odd number of nodes, duplicate the last one
            if i + 1 < len(current_level):
                right = current_level[i + 1]
            else:
                right = left

            # Combine and hash
            combined = left + right
            parent_hash = compute_hash(combined.encode('utf-8'))
            next_level.append(parent_hash)

        current_level = next_level

    return current_level[0]
