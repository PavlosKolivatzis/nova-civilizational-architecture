"""Static peer registry loader for federation scaffold."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, Optional

from nova.config.federation_config import FederationConfig, PeerEntry, load_federation_config, load_registry


@dataclass(frozen=True)
class PeerRecord:
    id: str
    url: str
    pubkey: str
    enabled: bool = True


class PeerRegistry:
    """Loads federation peers from YAML/ENV configuration."""

    def __init__(self, config: Optional[FederationConfig] = None) -> None:
        self._config = config or load_federation_config()
        self._peers: Dict[str, PeerRecord] = {}
        for entry in self._config.peers:
            self._insert(entry)

    @property
    def enabled(self) -> bool:
        return self._config.enabled

    @property
    def bind(self) -> str:
        return self._config.bind

    def records(self) -> Iterable[PeerRecord]:
        return tuple(self._peers.values())

    def get(self, peer_id: str) -> Optional[PeerRecord]:
        return self._peers.get(peer_id)

    def load_registry_file(self, path: Path) -> None:
        peers = load_registry(path)
        self._peers.clear()
        for entry in peers:
            self._insert(entry)

    def _insert(self, entry: PeerEntry) -> None:
        if not entry.id or not entry.url or not entry.pubkey:
            raise ValueError("Peer entries must include id, url, pubkey")
        if entry.id in self._peers:
            raise ValueError(f"Duplicate peer id: {entry.id}")
        self._peers[entry.id] = PeerRecord(
            id=entry.id,
            url=entry.url,
            pubkey=entry.pubkey,
            enabled=entry.enabled,
        )


__all__ = ["PeerRegistry", "PeerRecord"]
