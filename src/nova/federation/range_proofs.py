"""Utilities for federation range proof construction and verification.

Phase 15-3 scaffolds Merkle-style range proofs so peers can perform
bounded catch-up without downloading full checkpoint history.  The
current implementation focuses on deterministic chunking, continuity
validation, and hashed digests for integrity.  It is intentionally
minimal so that future phases can swap in full Merkle accumulators
without breaking the external protocol.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from typing import Iterable, List, Sequence, Tuple

from nova.federation.schemas import ProofChunk, RangeProofRequest, RangeProofResponse, TipSummary


@dataclass(frozen=True)
class RangeEntry:
    """Single checkpoint entry used to build a range proof."""

    height: int
    merkle_root: str


def _digest_roots(roots: Sequence[str]) -> str:
    digest = hashlib.sha3_256()
    for root in roots:
        digest.update(root.encode("ascii"))
    return digest.hexdigest()


def chunk_entries(
    entries: Sequence[RangeEntry],
    *,
    max_count: int,
    max_chunk_size: int,
) -> List[ProofChunk]:
    """Chunk ordered checkpoint entries into bounded proof chunks."""
    if not entries:
        return []

    limited_entries = entries[:max_count]
    chunks: List[ProofChunk] = []

    idx = 0
    total = len(limited_entries)
    while idx < total:
        window = limited_entries[idx : idx + max_chunk_size]
        start = window[0].height
        end = window[-1].height
        roots = [entry.merkle_root for entry in window]
        digest = _digest_roots(roots)
        chunk = ProofChunk(start=start, end=end, roots=roots, proof=[digest])
        chunks.append(chunk)
        idx += max_chunk_size

    return chunks


def build_range_response(
    entries: Sequence[RangeEntry],
    request: RangeProofRequest,
    *,
    tip: TipSummary,
    max_chunk_size: int,
) -> RangeProofResponse:
    """Construct a range proof response for the given request and entries."""
    chunks = chunk_entries(
        entries,
        max_count=request.max,
        max_chunk_size=max_chunk_size,
    )
    return RangeProofResponse(chunks=chunks, tip=tip)


def verify_chunk(chunk: ProofChunk) -> bool:
    """Verify an individual proof chunk digest."""
    if chunk.start > chunk.end:
        return False
    if len(chunk.roots) != (chunk.end - chunk.start + 1):
        return False
    if not chunk.proof:
        return False
    expected = _digest_roots(chunk.roots)
    return chunk.proof[0] == expected


def verify_response(
    response: RangeProofResponse,
    *,
    expected_start: int,
) -> Tuple[bool, List[ProofChunk]]:
    """
    Verify the provided range proof response.

    Returns:
        (ok, invalid_chunks) where invalid_chunks is a list of any chunks
        that failed verification.
    """
    invalid: List[ProofChunk] = []

    if not response.chunks:
        return True, invalid

    first_chunk = response.chunks[0]
    if first_chunk.start != expected_start:
        invalid.append(first_chunk)
        return False, invalid

    prev_end = first_chunk.start - 1
    for chunk in response.chunks:
        if chunk.start != prev_end + 1:
            invalid.append(chunk)
        elif not verify_chunk(chunk):
            invalid.append(chunk)
        prev_end = chunk.end

    if prev_end != response.tip.height:
        return False, invalid
    if response.tip.merkle_root != response.chunks[-1].roots[-1]:
        invalid.append(response.chunks[-1])

    return len(invalid) == 0, invalid


__all__ = [
    "RangeEntry",
    "chunk_entries",
    "build_range_response",
    "verify_chunk",
    "verify_response",
]
