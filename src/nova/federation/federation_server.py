"""FastAPI router for federation endpoints (Phase 15-1 scaffold)."""

from __future__ import annotations

import json
import os
import time
from collections import defaultdict, deque
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from pydantic import ValidationError

try:  # pragma: no cover - FastAPI optional in some environments
    from fastapi import APIRouter, Request, status
    from fastapi.responses import JSONResponse
except Exception:  # pragma: no cover
    APIRouter = None  # type: ignore

from nova.federation.peer_registry import PeerRegistry
from nova.federation.schemas import CheckpointEnvelope
from nova.federation.trust_model import score_trust
from nova.metrics import federation as federation_metrics


def _feature_enabled() -> bool:
    return os.getenv("FEDERATION_ENABLED", "false").lower() in {"1", "true", "yes", "on"}


def _error(code: str, http_status: int, reason: str) -> JSONResponse:
    return JSONResponse(status_code=http_status, content={"code": code, "reason": reason})


def build_router(peer_registry: Optional[PeerRegistry] = None) -> Optional[APIRouter]:
    if APIRouter is None or not _feature_enabled():
        return None

    registry = peer_registry or PeerRegistry()
    router = APIRouter(prefix="/federation", tags=["federation"])

    body_limit = int(os.getenv("NOVA_FEDERATION_BODY_MAX", str(64 * 1024)))
    skew_seconds = int(os.getenv("NOVA_FEDERATION_SKEW_S", "120"))
    replay_mode = os.getenv("NOVA_FEDERATION_REPLAY_MODE", "block").lower()
    replay_cache_size = int(os.getenv("NOVA_FEDERATION_REPLAY_CACHE_SIZE", "4096"))
    replay_cache: deque[str] = deque(maxlen=replay_cache_size)

    rate_rps = float(os.getenv("NOVA_FEDERATION_RATE_RPS", "0.5"))
    rate_burst = float(os.getenv("NOVA_FEDERATION_RATE_BURST", "30"))
    rate_buckets: defaultdict[str, Dict[str, float]] = defaultdict(
        lambda: {"t": time.monotonic(), "tokens": rate_burst}
    )

    def _set_peer_metrics() -> None:
        for record in registry.records():
            federation_metrics.set_peer_up(record.id, 1 if record.enabled else 0)

    _set_peer_metrics()

    def _lookup_peer(peer_id: str):
        return registry.get(peer_id)

    def _check_clock_skew(envelope: CheckpointEnvelope) -> tuple[bool, Optional[str]]:
        ts = envelope.ts.astimezone(timezone.utc) if envelope.ts.tzinfo else envelope.ts.replace(tzinfo=timezone.utc)
        delta = (datetime.now(timezone.utc) - ts).total_seconds()
        if abs(delta) <= skew_seconds:
            return True, None
        return False, "stale" if delta > 0 else "future"

    def _rate_allow(peer_id: str) -> bool:
        bucket = rate_buckets[peer_id]
        now = time.monotonic()
        elapsed = now - bucket["t"]
        bucket["t"] = now
        bucket["tokens"] = min(rate_burst, bucket["tokens"] + elapsed * rate_rps)
        if bucket["tokens"] < 1.0:
            return False
        bucket["tokens"] -= 1.0
        return True

    def _register_success(peer_id: str) -> None:
        federation_metrics.inc_verified("ok", peer_id)
        federation_metrics.set_last_sync(peer_id, 0.0)

    def _register_failure(peer_id: str = "unknown") -> None:
        federation_metrics.inc_verified("fail", peer_id)

    def _replay_key(envelope: CheckpointEnvelope) -> str:
        return "|".join(
            [
                str(envelope.anchor_id),
                str(envelope.height),
                envelope.merkle_root,
                envelope.producer,
            ]
        )

    @router.get("/health")
    async def health() -> Dict[str, Any]:
        return {
            "status": "ok" if registry.enabled else "disabled",
            "enabled": registry.enabled,
            "bind": registry.bind,
            "peer_count": len(tuple(registry.records())),
        }

    @router.get("/peers")
    async def list_peers() -> Dict[str, Any]:
        peers = [
            {"id": record.id, "url": record.url, "pubkey": record.pubkey, "enabled": record.enabled}
            for record in registry.records()
        ]
        return {"peers": peers}

    @router.post("/checkpoint")
    async def submit_checkpoint(request: Request) -> JSONResponse:
        content_type = request.headers.get("content-type", "").split(";")[0].strip().lower()
        if content_type != "application/json":
            return _error(
                "unsupported_media_type",
                status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
                "Content-Type must be application/json",
            )

        content_length = request.headers.get("content-length")
        if content_length and content_length.isdigit() and int(content_length) > body_limit:
            return _error("too_large", status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, "Body exceeds configured limit")

        try:
            payload = await request.json()
        except Exception:  # pragma: no cover - malformed payload
            return _error("invalid_json", status.HTTP_400_BAD_REQUEST, "Malformed JSON body")

        try:
            envelope = CheckpointEnvelope(**payload)
        except ValidationError:
            return _error("invalid_payload", status.HTTP_422_UNPROCESSABLE_ENTITY, "Invalid checkpoint payload")

        ok_skew, skew_reason = _check_clock_skew(envelope)
        if not ok_skew:
            return _error(skew_reason or "skew", status.HTTP_422_UNPROCESSABLE_ENTITY, f"Clock skew: {skew_reason}")

        peer = _lookup_peer(envelope.producer)
        if peer is None:
            _register_failure()
            return _error("unknown_peer", status.HTTP_401_UNAUTHORIZED, "Unknown peer")

        if not _rate_allow(peer.id):
            _register_failure(peer.id)
            return _error("rate_limited", status.HTTP_429_TOO_MANY_REQUESTS, "Too many requests")

        replayed = False
        replay_key = _replay_key(envelope)
        if replay_key in replay_cache:
            if replay_mode == "block":
                _register_failure(peer.id)
                return _error("replay", status.HTTP_409_CONFLICT, "Duplicate checkpoint")
            if replay_mode == "mark":
                replayed = True
        else:
            replay_cache.append(replay_key)

        # TODO: integrate Dilithium + Merkle verification in Phase 15-2.
        trust = score_trust(True)
        _register_success(peer.id)
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "peer": peer.id,
                "trust": trust,
                "canonical_ts": envelope.canonical_ts(),
                "replayed": replayed,
            },
        )

    @router.post("/verify")
    async def verify_checkpoint(request: Request) -> JSONResponse:
        try:
            payload = await request.json()
        except Exception:  # pragma: no cover - malformed payload
            return _error("invalid_json", status.HTTP_400_BAD_REQUEST, "Malformed JSON body")

        try:
            envelope = CheckpointEnvelope(**payload)
        except ValidationError:
            return _error("invalid_payload", status.HTTP_422_UNPROCESSABLE_ENTITY, "Invalid checkpoint payload")

        peer = _lookup_peer(envelope.producer)
        peer_id = peer.id if peer else "unknown"
        trust = score_trust(True)
        _register_success(peer_id)
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={"verified": trust["verified"], "score": trust["score"]},
        )

    return router


__all__ = ["build_router"]
