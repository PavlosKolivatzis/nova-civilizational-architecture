"""Peer manifest discovery and verification."""

from __future__ import annotations

import json
import time
from dataclasses import dataclass
from typing import Dict, Optional

from nova.crypto.pqc_keyring import PQCKeyring
from nova.federation.schemas import KeyRotationReceipt, PeerManifest
from nova.federation.receipts import build_key_rotation_receipt


def _canonical_manifest_payload(manifest: PeerManifest) -> bytes:
    data = manifest.model_dump(
        mode="json",
        by_alias=True,
        exclude={"sig"},
    )
    return json.dumps(data, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("ascii")


class ManifestVerificationError(RuntimeError):
    """Raised when a peer manifest fails verification."""


class ManifestVerifier:
    """Verify peer manifests signed with Dilithium2 keys."""

    def __init__(self, keyring: Optional[PQCKeyring] = None) -> None:
        self._keyring = keyring or PQCKeyring()

    def verify(self, manifest: PeerManifest) -> None:
        if not manifest.keys:
            raise ManifestVerificationError("manifest missing keys")
        active_key = manifest.keys[-1]
        try:
            pub = PQCKeyring.decode_key(active_key.pub)
            sig = PQCKeyring.decode_signature(manifest.sig)
        except Exception as exc:  # pragma: no cover - defensive
            raise ManifestVerificationError("manifest contains invalid base64") from exc

        payload = _canonical_manifest_payload(manifest)
        if not self._keyring.verify(pub, payload, sig):
            raise ManifestVerificationError("manifest signature invalid")


@dataclass
class ManifestCacheEntry:
    manifest: PeerManifest
    fetched_at: float


class ManifestCache:
    """In-memory cache for manifests with TTL control."""

    def __init__(self, ttl_seconds: int) -> None:
        self._ttl = ttl_seconds
        self._cache: Dict[str, ManifestCacheEntry] = {}

    def get(self, peer_id: str) -> Optional[PeerManifest]:
        entry = self._cache.get(peer_id)
        if not entry:
            return None
        if time.time() - entry.fetched_at > self._ttl:
            self._cache.pop(peer_id, None)
            return None
        return entry.manifest

    def set(self, peer_id: str, manifest: PeerManifest) -> None:
        self._cache[peer_id] = ManifestCacheEntry(manifest=manifest, fetched_at=time.time())


def detect_rotation(
    peer_id: str,
    manifest: PeerManifest,
    previous: Optional[PeerManifest],
) -> Optional[KeyRotationReceipt]:
    """Generate a key rotation receipt if the manifest introduces a new key id."""
    if not manifest.keys:
        return None
    latest = manifest.keys[-1]
    if previous and previous.keys and previous.keys[-1].kid == latest.kid:
        return None
    return build_key_rotation_receipt(peer_id, manifest)


__all__ = [
    "ManifestVerificationError",
    "ManifestVerifier",
    "ManifestCache",
    "detect_rotation",
]
