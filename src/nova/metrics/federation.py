"""Prometheus metrics accessors for federation scaffold."""

from __future__ import annotations

from typing import Dict, Tuple

from prometheus_client import Counter, Gauge

from .registry import REGISTRY

_verifications = Counter(
    "federation_verifications_total",
    "Federation checkpoint verifications by result/peer",
    ("result", "peer"),
    registry=REGISTRY,
)
_peers_up = Gauge(
    "federation_peers_up",
    "Configured peers marked as enabled",
    ("peer",),
    registry=REGISTRY,
)
_last_sync = Gauge(
    "federation_last_sync_seconds",
    "Seconds since last successful sync per peer",
    ("peer",),
    registry=REGISTRY,
)


def inc_verified(result: str, peer: str) -> None:
    _verifications.labels(result=result, peer=peer).inc()


def set_peer_up(peer: str, up: int) -> None:
    _peers_up.labels(peer=peer).set(float(up))


def set_last_sync(peer: str, seconds: float) -> None:
    _last_sync.labels(peer=peer).set(seconds)


def verifications_counter() -> Counter:
    return _verifications


def reset_for_tests() -> None:
    """Reset counters and gauges between tests."""
    _verifications._metrics.clear()  # type: ignore[attr-defined]
    _peers_up._metrics.clear()  # type: ignore[attr-defined]
    _last_sync._metrics.clear()  # type: ignore[attr-defined]


__all__ = [
    "inc_verified",
    "set_peer_up",
    "set_last_sync",
    "verifications_counter",
    "reset_for_tests",
]
