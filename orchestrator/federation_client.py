"""Thin orchestration helpers for federation polling."""

from __future__ import annotations

import os
from typing import Dict, List, Optional

from nova.federation.federation_client import FederationClient
from nova.federation.peer_registry import PeerRecord


def get_peer_list(*, timeout: Optional[float] = None) -> List[PeerRecord]:
    """Return enabled peers from the static registry."""
    if _force_errors_enabled():
        raise RuntimeError("dev-forced federation failure")
    client = FederationClient(timeout_s=timeout) if timeout is not None else FederationClient()
    try:
        peers = list(client.list_peers().values())
        return peers
    finally:
        client.close()


def get_verified_checkpoint(*, timeout: Optional[float] = None) -> Optional[Dict[str, object]]:
    """Fetch the most recent checkpoint envelope from any reachable peer."""
    if _force_errors_enabled():
        raise RuntimeError("dev-forced federation failure")
    client = FederationClient(timeout_s=timeout) if timeout is not None else FederationClient()
    try:
        best: Optional[Dict[str, object]] = None
        for peer in client.list_peers().values():
            try:
                envelope = client.fetch_latest(peer)
            except Exception:
                continue
            if envelope is None:
                continue
            candidate = {
                "height": envelope.height,
                "producer": envelope.producer,
                "ts": envelope.canonical_ts(),
            }
            if best is None or candidate["height"] > best["height"]:
                best = candidate
        return best
    finally:
        client.close()


def _force_errors_enabled() -> bool:
    return os.getenv("NOVA_FED_FORCE_ERRORS", "0").strip() == "1"

