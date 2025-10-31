"""Peer registry loading tests."""

from __future__ import annotations

from pathlib import Path

import pytest

from nova.config.federation_config import FederationConfig, PeerEntry
from nova.federation.peer_registry import PeerRegistry


@pytest.mark.health
def test_registry_loads_minimal(tmp_path: Path):
    cfg = FederationConfig(
        enabled=True,
        peers=[PeerEntry(id="node-athens", url="https://athens.example.net", pubkey=str(tmp_path / "a.pem"))],
    )
    registry = PeerRegistry(cfg)
    record = registry.get("node-athens")
    assert record is not None
    assert record.url == "https://athens.example.net"


def test_duplicate_peer_ids_raise(tmp_path: Path):
    cfg = FederationConfig(
        peers=[
            PeerEntry(id="dup", url="https://a", pubkey=str(tmp_path / "a.pem")),
            PeerEntry(id="dup", url="https://b", pubkey=str(tmp_path / "b.pem")),
        ]
    )
    with pytest.raises(ValueError):
        PeerRegistry(cfg)
