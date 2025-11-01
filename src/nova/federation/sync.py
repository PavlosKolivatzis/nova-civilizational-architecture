"""Client-side range synchronisation helpers."""

from __future__ import annotations

import os
from collections import defaultdict
from contextlib import contextmanager
from typing import Dict, Optional, Tuple

try:  # pragma: no cover - optional dependency
    from opentelemetry import trace
except Exception:  # pragma: no cover
    trace = None

from nova.federation.discovery import ManifestCache, ManifestVerifier, detect_rotation, ManifestVerificationError
from nova.federation.federation_client import FederationClient
from nova.federation.peer_registry import PeerRecord
from nova.federation.range_proofs import verify_response
from nova.federation.receipts import build_continuity_receipt, build_divergence_receipt
from nova.federation.schemas import PeerManifest, RangeProofRequest, RangeProofResponse
from nova.ledger.receipts_store import ReceiptsStore
from nova.metrics import federation as federation_metrics


@contextmanager
def _start_span(name: str):
    if trace is None:  # pragma: no cover
        yield None
        return
    tracer = trace.get_tracer("nova.federation")
    with tracer.start_as_current_span(name) as span:
        yield span


class RangeSyncError(RuntimeError):
    """Raised when a range sync operation fails."""


class RangeQuarantineError(RangeSyncError):
    """Raised when divergence exceeds configured limit."""


class RangeSyncer:
    """Fetch and verify range proofs from peers, recording receipts."""

def _default_manifest_cache() -> ManifestCache:
    raw = os.getenv("NOVA_FEDERATION_MANIFEST_TTL_S", "3600")
    try:
        ttl = int(raw)
    except ValueError:
        ttl = 3600
    return ManifestCache(ttl_seconds=ttl)


def _default_divergence_limit() -> int:
    raw = os.getenv("NOVA_FEDERATION_MAX_DIVERGENCE", "2")
    try:
        value = int(raw)
    except ValueError:
        value = 2
    return max(1, value)


class RangeSyncer:
    """Fetch and verify range proofs from peers, recording receipts."""

    def __init__(
        self,
        client: FederationClient,
        receipts: ReceiptsStore,
        *,
        range_limit: int,
        divergence_limit: Optional[int] = None,
        manifest_cache: Optional[ManifestCache] = None,
        manifest_verifier: Optional[ManifestVerifier] = None,
    ) -> None:
        self._client = client
        self._receipts = receipts
        self._range_limit = range_limit
        self._divergence_limit = max(1, divergence_limit) if divergence_limit is not None else _default_divergence_limit()
        self._manifest_cache = manifest_cache or _default_manifest_cache()
        self._manifest_verifier = manifest_verifier or ManifestVerifier()
        self._divergence_counts: Dict[str, int] = defaultdict(int)

    def sync(self, peer: PeerRecord, start_height: int) -> RangeProofResponse:
        with _start_span("federation.sync"):
            self._ensure_manifest(peer)
            request = RangeProofRequest(from_height=start_height, max=self._range_limit)
            response = self._client.fetch_range(peer, request)
            ok, invalid_chunks = verify_response(response, expected_start=start_height)
            byte_count = len(response.model_dump_json(by_alias=True).encode("utf-8"))
            federation_metrics.add_range_bytes(peer.id, byte_count)

            if not ok:
                for chunk in invalid_chunks or [response.chunks[0] if response.chunks else None]:
                    if chunk:
                        federation_metrics.inc_range_chunk(peer.id, "fail")
                federation_metrics.inc_divergence(peer.id)
                expected_root = response.tip.merkle_root
                if invalid_chunks:
                    divergence_height = invalid_chunks[0].start
                    observed_root = invalid_chunks[0].roots[-1] if invalid_chunks[0].roots else "unknown"
                else:
                    divergence_height = start_height
                    observed_root = "unknown"
                receipt = build_divergence_receipt(
                    peer.id,
                    divergence_height=divergence_height,
                    expected_root=expected_root,
                    observed_root=observed_root,
                    tip=response.tip,
                )
                self._receipts.append(receipt.model_dump(mode="json"))
                self._divergence_counts[peer.id] += 1
                if self._divergence_counts[peer.id] > self._divergence_limit:
                    raise RangeQuarantineError(f"peer {peer.id} exceeded divergence threshold")
                raise RangeSyncError("Range verification failed")

            for chunk in response.chunks:
                federation_metrics.inc_range_chunk(peer.id, "ok")

            receipt = build_continuity_receipt(
                peer.id,
                range_start=start_height,
                range_end=response.tip.height,
                tip=response.tip,
                status="ok",
                details={"chunks": len(response.chunks)},
            )
            self._receipts.append(receipt.model_dump(mode="json"))
            self._divergence_counts[peer.id] = 0
            return response

    def _ensure_manifest(self, peer: PeerRecord) -> Optional[PeerManifest]:
        cached = self._manifest_cache.get(peer.id)
        if cached:
            return cached
        with _start_span("federation.manifest.fetch"):
            manifest = self._client.fetch_manifest(peer)
            if manifest is None:
                return None
            try:
                self._manifest_verifier.verify(manifest)
            except ManifestVerificationError as exc:  # pragma: no cover - defensive
                raise RangeSyncError(f"Manifest verification failed for {peer.id}: {exc}") from exc
            previous = cached
            self._manifest_cache.set(peer.id, manifest)
            receipt = detect_rotation(peer.id, manifest, previous)
            if receipt:
                self._receipts.append(receipt.model_dump(mode="json"))
                federation_metrics.inc_manifest_rotation(peer.id)
            return manifest


__all__ = ["RangeSyncer", "RangeSyncError", "RangeQuarantineError"]
