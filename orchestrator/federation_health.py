"""Federation readiness and health helpers."""

from __future__ import annotations

import os
from time import time
from typing import Dict, List

from nova.federation.metrics import m


def _label_map(gauge, labels) -> Dict[str, str]:
    return dict(zip(gauge._labelnames, labels))  # type: ignore[attr-defined]


def get_peer_health() -> Dict[str, object]:
    """Return current federation metrics in a JSON-friendly form."""
    metrics = m()
    ready_gauge = metrics.get("ready")
    ready_value = ready_gauge._value.get() if ready_gauge else 0.0
    ready = ready_value >= 1.0

    height_gauge = metrics.get("height")
    height = int(height_gauge._value.get()) if height_gauge else 0

    peer_up = metrics.get("peer_up")
    peer_last_seen = metrics.get("peer_last_seen")
    peers: List[Dict[str, object]] = []
    if peer_up and getattr(peer_up, "_metrics", None):
        for labels in peer_up._metrics.keys():  # type: ignore[attr-defined]
            label_map = _label_map(peer_up, labels)
            peer_id = label_map.get("peer")
            if not peer_id:
                continue
            up_value = peer_up.labels(**label_map)._value.get()
            last_seen_value = 0.0
            if peer_last_seen:
                try:
                    last_seen_value = peer_last_seen.labels(**label_map)._value.get()
                except KeyError:
                    last_seen_value = 0.0
            peers.append(
                {
                    "id": peer_id,
                    "state": "up" if up_value >= 1.0 else "unknown",
                    "last_seen": last_seen_value,
                }
            )

    return {
        "ready": ready,
        "peers": peers,
        "checkpoint": {"height": height},
    }


def is_ready(threshold_seconds: float = 120.0) -> bool:
    """Return True when federation is considered ready for traffic."""
    info = get_peer_health()
    if not info["ready"]:
        return False
    if not info["peers"]:
        return False
    last_success = m()["last_result_ts"].labels(status="success")._value.get()
    if not last_success:
        return False
    return (time() - last_success) < threshold_seconds
