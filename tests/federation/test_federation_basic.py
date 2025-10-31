"""Phase 15-1 federation scaffold tests."""

from __future__ import annotations

from pydantic import ValidationError

import base64
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

import pytest

from nova.config.federation_config import load_federation_config
from nova.federation.peer_registry import PeerRegistry
from nova.federation.schemas import CheckpointEnvelope, Peer
from nova.federation.trust_model import score_trust


def test_feature_flag_disabled(monkeypatch):
    monkeypatch.setenv("FEDERATION_ENABLED", "false")
    from nova.federation.federation_server import build_router

    router = build_router()
    assert router is None


def test_peer_schema_coerces_path():
    peer = Peer(id="node-a", url="https://node-a.example.org", pubkey_path="keys/a.pem")
    assert isinstance(peer.pubkey_path, Path)
    assert peer.pubkey_path.as_posix() == "keys/a.pem"


def test_score_trust_binary():
    assert score_trust(True) == {"verified": True, "score": 1.0}
    assert score_trust(False) == {"verified": False, "score": 0.0}


def test_registry_loads_yaml(tmp_path: Path, monkeypatch):
    registry_file = tmp_path / "peers.yaml"
    registry_file.write_text(
        """
        federation:
          peers:
            - id: node-a
              url: https://node-a.example.org
              pubkey: keys/a.pem
        """,
        encoding="utf-8",
    )
    monkeypatch.setenv("FEDERATION_ENABLED", "true")
    monkeypatch.setenv("NOVA_FEDERATION_REGISTRY", str(registry_file))
    config = load_federation_config()
    registry = PeerRegistry(config)
    record = registry.get("node-a")
    assert record is not None
    assert record.url == "https://node-a.example.org"


def test_checkpoint_envelope_canonical_json():
    sig = base64.b64encode(b"x" * 600).decode()
    envelope = CheckpointEnvelope(
        anchor_id=uuid4(),
        merkle_root="a" * 64,
        height=42,
        ts=datetime.now(timezone.utc),
        sig_b64=sig,
        producer="node-a",
    )
    canonical = envelope.canonical_json()
    assert canonical == envelope.canonical_bytes().decode("ascii")
    assert " " not in canonical  # no whitespace
    assert canonical.startswith("{") and canonical.endswith("}")


def test_checkpoint_envelope_invalid_merkle():
    sig = base64.b64encode(b"x" * 600).decode()
    with pytest.raises(ValidationError):
        CheckpointEnvelope(
            anchor_id=uuid4(),
            merkle_root="zzz",
            height=0,
            ts=datetime.now(timezone.utc),
            sig_b64=sig,
            producer="node-a",
        )


def test_checkpoint_envelope_invalid_signature_length():
    bad_sig = "AAAA" * 100  # 400 chars < 800
    with pytest.raises(ValidationError):
        CheckpointEnvelope(
            anchor_id=uuid4(),
            merkle_root="b" * 64,
            height=0,
            ts=datetime.now(timezone.utc),
            sig_b64=bad_sig,
            producer="node-a",
        )
