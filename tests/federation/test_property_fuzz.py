"""Property-based tests for federation schemas."""

from __future__ import annotations

import base64

from hypothesis import given, strategies as st

from nova.federation.schemas import CheckpointEnvelope

hex64 = st.text(alphabet="0123456789abcdef", min_size=64, max_size=64)
bytes_strategy = st.binary(min_size=600, max_size=3000)


@given(merkle=hex64, sig_bytes=bytes_strategy)
def test_envelope_accepts_valid_ranges(merkle, sig_bytes):
    sig_b64 = base64.b64encode(sig_bytes).decode()
    env = CheckpointEnvelope(
        anchor_id="00000000-0000-0000-0000-000000000000",
        merkle_root=merkle,
        height=1,
        ts="2025-10-31T12:00:00Z",
        sig_b64=sig_b64,
        producer="node-athens",
    )
    canonical = env.canonical_json()
    assert canonical.startswith("{") and canonical.endswith("}")
