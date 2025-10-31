"""Schema validation and canonical JSON tests."""

from __future__ import annotations

import base64
import json

import pytest
from pydantic import ValidationError

from nova.federation.schemas import CheckpointEnvelope


@pytest.mark.health
def test_canonical_json_stable(make_envelope):
    envelope = make_envelope()
    canonical = envelope.canonical_json()
    assert canonical == envelope.canonical_bytes().decode("ascii")
    # Ensure deterministic ordering and compact separators
    assert canonical == json.dumps(json.loads(canonical), sort_keys=True, separators=(",", ":"))
    assert " " not in canonical


@pytest.mark.health
def test_canonical_timestamp_utc_seconds(make_envelope):
    envelope = make_envelope()
    ts = envelope.canonical_ts()
    assert ts.endswith("Z")
    assert "." not in ts.split("T", 1)[1]


@pytest.mark.health
@pytest.mark.parametrize("length", [63, 65])
def test_merkle_root_enforces_length(make_envelope, length):
    with pytest.raises(ValidationError):
        make_envelope(merkle_root="a" * length)


@pytest.mark.health
def test_signature_length_window(make_envelope):
    too_small = base64.b64encode(b"x" * 100).decode()
    with pytest.raises(ValidationError):
        make_envelope(sig_b64=too_small)
    too_large = base64.b64encode(b"x" * 3500).decode()
    with pytest.raises(ValidationError):
        make_envelope(sig_b64=too_large)
    ok = make_envelope()
    assert 800 <= len(ok.sig_b64) <= 4000
