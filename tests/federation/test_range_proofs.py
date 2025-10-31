from datetime import datetime, timezone

from nova.federation.range_proofs import RangeEntry, build_range_response, verify_response
from nova.federation.schemas import RangeProofRequest, TipSummary


def make_entries(count: int, start: int = 0) -> list[RangeEntry]:
    return [
        RangeEntry(height=start + idx, merkle_root=f"{idx:064x}")
        for idx in range(count)
    ]


def test_build_range_response_basic():
    entries = make_entries(12, start=5)
    request = RangeProofRequest(from_height=5, max=12)
    tip = TipSummary(
        height=5 + len(entries) - 1,
        merkle_root=entries[-1].merkle_root,
        ts=datetime.now(timezone.utc),
        producer="node-athens",
    )
    response = build_range_response(entries, request, tip=tip, max_chunk_size=5)
    assert len(response.chunks) == 3
    assert response.chunks[0].start == 5
    assert response.chunks[-1].end == tip.height

    ok, invalid = verify_response(response, expected_start=5)
    assert ok
    assert not invalid


def test_range_response_detects_tampering():
    entries = make_entries(6, start=10)
    request = RangeProofRequest(from_height=10, max=6)
    tip = TipSummary(
        height=entries[-1].height,
        merkle_root=entries[-1].merkle_root,
        ts=datetime.now(timezone.utc),
        producer="node-athens",
    )
    response = build_range_response(entries, request, tip=tip, max_chunk_size=4)
    response.chunks[0].roots[0] = "f" * 64
    ok, invalid = verify_response(response, expected_start=10)
    assert not ok
    assert invalid
