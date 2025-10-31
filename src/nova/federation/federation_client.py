"""Federation client for outbound peer communication."""

from __future__ import annotations

import os
import random
import time
from typing import Dict, Optional

import httpx

from nova.federation.peer_registry import PeerRecord, PeerRegistry
from nova.federation.schemas import (
    CheckpointEnvelope,
    PeerManifest,
    RangeProofRequest,
    RangeProofResponse,
)
from nova.metrics import federation as federation_metrics


def _default_timeout() -> float:
    return float(os.getenv("NOVA_FEDERATION_HTTP_TIMEOUT_S", "2.5"))


def _default_retries() -> int:
    return int(os.getenv("NOVA_FEDERATION_RETRIES", "2"))


class FederationClient:
    """HTTP client for federation endpoints."""

    def __init__(
        self,
        registry: Optional[PeerRegistry] = None,
        *,
        timeout_s: Optional[float] = None,
        retries: Optional[int] = None,
    ) -> None:
        self._registry = registry or PeerRegistry()
        self._timeout = timeout_s if timeout_s is not None else _default_timeout()
        self._retries = retries if retries is not None else _default_retries()
        self._client = httpx.Client(timeout=self._timeout)

    def close(self) -> None:
        self._client.close()

    def __enter__(self) -> "FederationClient":  # pragma: no cover - convenience
        return self

    def __exit__(self, *exc_info) -> None:  # pragma: no cover - convenience
        self.close()

    def list_peers(self) -> Dict[str, PeerRecord]:
        return {peer.id: peer for peer in self._registry.records() if peer.enabled}

    def fetch_latest(self, peer: PeerRecord) -> Optional[CheckpointEnvelope]:
        url = peer.url.rstrip("/") + "/federation/checkpoints/latest"
        try:
            response = self._request("GET", url, peer.id)
        except httpx.HTTPError:
            return None
        if response.status_code == 204:
            return None
        return CheckpointEnvelope(**response.json())

    def fetch_range(self, peer: PeerRecord, request: RangeProofRequest) -> RangeProofResponse:
        url = peer.url.rstrip("/") + "/federation/range_proof"
        response = self._request(
            "POST",
            url,
            peer.id,
            json=request.model_dump(mode="json"),
            headers={"Content-Type": "application/json"},
        )
        return RangeProofResponse(**response.json())

    def fetch_manifest(self, peer: PeerRecord) -> Optional[PeerManifest]:
        url = peer.url.rstrip("/") + "/.well-known/nova-peer.json"
        try:
            response = self._request("GET", url, peer.id)
        except httpx.HTTPError:
            return None
        return PeerManifest(**response.json())

    def submit_checkpoint(self, peer: PeerRecord, envelope: CheckpointEnvelope) -> Dict[str, object]:
        url = peer.url.rstrip("/") + "/federation/checkpoint"
        response = self._request(
            "POST",
            url,
            peer.id,
            json=envelope.model_dump(mode="json"),
            headers={"Content-Type": "application/json"},
        )
        return response.json()

    def _request(self, method: str, url: str, peer_id: str, **kwargs) -> httpx.Response:
        attempt = 0
        while True:
            try:
                response = self._client.request(method, url, **kwargs)
                if response.status_code >= 500 and attempt < self._retries:
                    attempt += 1
                    federation_metrics.inc_client_retry(peer_id)
                    time.sleep(random.uniform(0.05, 0.15))
                    continue
                response.raise_for_status()
                return response
            except (httpx.TimeoutException, httpx.RequestError) as exc:
                if attempt >= self._retries:
                    raise
                attempt += 1
                federation_metrics.inc_client_retry(peer_id)
                time.sleep(random.uniform(0.05, 0.15))
                continue


__all__ = ["FederationClient"]
