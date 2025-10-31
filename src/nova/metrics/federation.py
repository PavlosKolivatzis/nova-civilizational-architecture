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
_score_gauge = Gauge(
    "federation_score_gauge",
    "Gradient trust score per peer",
    ("peer",),
    registry=REGISTRY,
)
_client_retries = Counter(
    "federation_client_retries_total",
    "Federation client retry attempts per peer",
    ("peer",),
    registry=REGISTRY,
)
_range_bytes = Counter(
    "federation_range_bytes_total",
    "Total bytes transferred during range proofs",
    ("peer",),
    registry=REGISTRY,
)
_range_chunks = Counter(
    "federation_range_chunks_total",
    "Range proof chunks processed by result/peer",
    ("peer", "result"),
    registry=REGISTRY,
)
_divergences = Counter(
    "federation_divergences_total",
    "Detected divergence events per peer",
    ("peer",),
    registry=REGISTRY,
)
_manifest_rotations = Counter(
    "federation_manifest_rotations_total",
    "Manifest rotations recorded per peer",
    ("peer",),
    registry=REGISTRY,
)


def inc_verified(result: str, peer: str) -> None:
    _verifications.labels(result=result, peer=peer).inc()


def set_peer_up(peer: str, up: int) -> None:
    _peers_up.labels(peer=peer).set(float(up))


def set_last_sync(peer: str, seconds: float) -> None:
    _last_sync.labels(peer=peer).set(seconds)


def set_score(peer: str, score: float) -> None:
    _score_gauge.labels(peer=peer).set(score)


def inc_client_retry(peer: str) -> None:
    _client_retries.labels(peer=peer).inc()


def add_range_bytes(peer: str, byte_count: int) -> None:
    _range_bytes.labels(peer=peer).inc(byte_count)


def inc_range_chunk(peer: str, result: str) -> None:
    _range_chunks.labels(peer=peer, result=result).inc()


def inc_divergence(peer: str) -> None:
    _divergences.labels(peer=peer).inc()


def inc_manifest_rotation(peer: str) -> None:
    _manifest_rotations.labels(peer=peer).inc()


def verifications_counter() -> Counter:
    return _verifications


def client_retries_counter() -> Counter:
    return _client_retries


def reset_for_tests() -> None:
    """Reset counters and gauges between tests."""
    _verifications._metrics.clear()  # type: ignore[attr-defined]
    _peers_up._metrics.clear()  # type: ignore[attr-defined]
    _last_sync._metrics.clear()  # type: ignore[attr-defined]
    _score_gauge._metrics.clear()  # type: ignore[attr-defined]
    _client_retries._metrics.clear()  # type: ignore[attr-defined]
    _range_bytes._metrics.clear()  # type: ignore[attr-defined]
    _range_chunks._metrics.clear()  # type: ignore[attr-defined]
    _divergences._metrics.clear()  # type: ignore[attr-defined]
    _manifest_rotations._metrics.clear()  # type: ignore[attr-defined]


__all__ = [
    "inc_verified",
    "set_peer_up",
    "set_last_sync",
    "set_score",
    "inc_client_retry",
    "add_range_bytes",
    "inc_range_chunk",
    "inc_divergence",
    "inc_manifest_rotation",
    "verifications_counter",
    "client_retries_counter",
    "reset_for_tests",
]
