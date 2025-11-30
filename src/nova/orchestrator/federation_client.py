"""Thin orchestration helpers for federation polling."""

from __future__ import annotations

import os
from time import perf_counter, time
from typing import Dict, List, Optional, Tuple

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


def get_peer_metrics(
    *, timeout: Optional[float] = None
) -> Tuple[List[PeerRecord], Optional[Dict[str, object]], Dict[str, Dict[str, object]]]:
    """Return peers, the best checkpoint, and per-peer latency/success metrics."""
    if _force_errors_enabled():
        raise RuntimeError("dev-forced federation failure")
    client = FederationClient(timeout_s=timeout) if timeout is not None else FederationClient()
    try:
        peers = list(client.list_peers().values())
        best: Optional[Dict[str, object]] = None
        peer_stats: Dict[str, Dict[str, object]] = {}
        for peer in peers:
            peer_id = getattr(peer, "id", str(peer))
            started = perf_counter()
            success = False
            envelope = None
            try:
                envelope = client.fetch_latest(peer)
            except Exception:
                envelope = None
            duration = perf_counter() - started
            if envelope is not None:
                success = True
                candidate = {
                    "height": envelope.height,
                    "producer": envelope.producer,
                    "ts": envelope.canonical_ts(),
                }
                if best is None or candidate["height"] > best["height"]:
                    best = candidate
            peer_stats[peer_id] = {
                "duration": duration,
                "success": success,
                "last_success_ts": time() if success else None,
            }
        return peers, best, peer_stats
    finally:
        client.close()


def _force_errors_enabled() -> bool:
    return os.getenv("NOVA_FED_FORCE_ERRORS", "0").strip() == "1"
