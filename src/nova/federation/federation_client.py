"""Placeholder federation client for Phase 15-1."""

from __future__ import annotations

from typing import Dict, Optional

from nova.federation.peer_registry import PeerRecord, PeerRegistry


class FederationClient:
    """Stub client that will perform HTTP exchanges in later phases."""

    def __init__(self, registry: Optional[PeerRegistry] = None) -> None:
        self._registry = registry or PeerRegistry()

    def list_peers(self) -> Dict[str, PeerRecord]:
        return {peer.id: peer for peer in self._registry.records()}


__all__ = ["FederationClient"]
