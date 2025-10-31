"""FastAPI router for federation endpoints (Phase 15-3)."""

from __future__ import annotations

import os
import time
from collections import defaultdict, deque
from contextlib import contextmanager
from datetime import datetime, timezone
from typing import Any, Dict, Iterable, Optional, Protocol, Sequence

from pydantic import BaseModel, ValidationError

try:  # pragma: no cover - FastAPI optional in some environments
    from fastapi import APIRouter, Request, Response, status
    from fastapi.responses import JSONResponse
except Exception:  # pragma: no cover
    APIRouter = None  # type: ignore

try:  # pragma: no cover - optional OpenTelemetry dependency
    from opentelemetry import trace
except Exception:  # pragma: no cover
    trace = None

from nova.federation.peer_registry import PeerRegistry, PeerRecord
from nova.federation.range_proofs import RangeEntry, build_range_response
from nova.federation.schemas import (
    CheckpointEnvelope,
    RangeProofRequest,
    RangeProofResponse,
    TipSummary,
)
from nova.federation.trust_model import compute_gradient_score
from nova.metrics import federation as federation_metrics


class RangeProvider(Protocol):
    """Protocol for accessing checkpoint ranges."""

    def tip(self) -> Optional[TipSummary]:
        ...

    def range_slice(self, start: int, limit: int) -> Sequence[RangeEntry]:
        ...


class _NullRangeProvider:
    def tip(self) -> Optional[TipSummary]:  # pragma: no cover - trivial
        return None

    def range_slice(self, start: int, limit: int) -> Sequence[RangeEntry]:  # pragma: no cover
        return ()


def _feature_enabled() -> bool:
    return os.getenv("FEDERATION_ENABLED", "false").lower() in {"1", "true", "yes", "on"}


def _error(code: str, http_status: int, reason: str) -> JSONResponse:
    return JSONResponse(status_code=http_status, content={"code": code, "reason": reason})


@contextmanager
def _start_span(name: str):
    if trace is None:  # pragma: no cover - tracing optional
        yield None
        return
    tracer = trace.get_tracer("nova.federation")
    with tracer.start_as_current_span(name) as span:
        yield span


def build_router(
    peer_registry: Optional[PeerRegistry] = None,
    *,
    range_provider: Optional[RangeProvider] = None,
) -> Optional[APIRouter]:
    if APIRouter is None or not _feature_enabled():
        return None

    registry = peer_registry or PeerRegistry()
    provider = range_provider or _NullRangeProvider()
    router = APIRouter(prefix="/federation", tags=["federation"])

    class TrustPayload(BaseModel):
        verified: bool
        score: float

    class CheckpointResponse(BaseModel):
        peer: str
        trust: TrustPayload
        canonical_ts: str
        replayed: bool = False

    CHECKPOINT_REQUEST_EXAMPLE = {
        "anchor_id": "00000000-0000-0000-0000-000000000000",
        "merkle_root": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
        "height": 42,
        "ts": "2025-10-31T00:00:00Z",
        "algo": "sha3-256",
        "sig_b64": "eHh4eHh4eHh4eHh4eHh4eHh4eHh4eHh4eXg=",
        "producer": "node-athens",
        "version": "v1",
    }

    ERROR_RESPONSES = {
        400: {"description": "Malformed request", "content": {"application/json": {"example": {"code": "invalid_json", "reason": "Malformed JSON body"}}}},
        401: {"description": "Unknown peer", "content": {"application/json": {"example": {"code": "unknown_peer", "reason": "Unknown peer"}}}},
        409: {"description": "Replay", "content": {"application/json": {"example": {"code": "replay", "reason": "Duplicate checkpoint"}}}},
        413: {"description": "Payload too large", "content": {"application/json": {"example": {"code": "too_large", "reason": "Body exceeds configured limit"}}}},
        415: {"description": "Unsupported media type", "content": {"application/json": {"example": {"code": "unsupported_media_type", "reason": "Content-Type must be application/json"}}}},
        422: {
            "description": "Validation error",
            "content": {
                "application/json": {
                    "examples": {
                        "stale": {"value": {"code": "stale", "reason": "Clock skew: stale"}},
                        "range": {"value": {"code": "range_too_large", "reason": "Requested range exceeds limit"}},
                    }
                }
            },
        },
        429: {"description": "Rate limited", "content": {"application/json": {"example": {"code": "rate_limited", "reason": "Too many requests"}}}},
    }

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
    range_limit = int(os.getenv("NOVA_FEDERATION_RANGE_MAX", "256"))
    chunk_size = max(1, min(range_limit, 64))
    chunk_bytes_limit = int(os.getenv("NOVA_FEDERATION_CHUNK_BYTES_MAX", str(64 * 1024)))

    def _set_peer_metrics() -> None:
        for record in registry.records():
            federation_metrics.set_peer_up(record.id, 1 if record.enabled else 0)

    _set_peer_metrics()

    def _lookup_peer(peer_id: str):
        return registry.get(peer_id)

    def _peer_from_request(request: Request) -> str:
        header_peer = request.headers.get("X-Nova-Peer")
        if header_peer:
            return header_peer
        return "anonymous"

    def _model_size_bytes(model: BaseModel) -> int:
        return len(model.model_dump_json(by_alias=True, exclude_none=True).encode("utf-8"))

    def _normalize_entries(items: Sequence[Any]) -> Sequence[RangeEntry]:
        normalized: list[RangeEntry] = []
        for item in items:
            if isinstance(item, RangeEntry):
                normalized.append(item)
            elif isinstance(item, dict):
                normalized.append(RangeEntry(height=item["height"], merkle_root=item["merkle_root"]))
            else:
                height, root = item  # type: ignore[misc]
                normalized.append(RangeEntry(height=height, merkle_root=root))
        return normalized

    def _normalize_tip(raw_tip: Any) -> Optional[TipSummary]:
        if raw_tip is None:
            return None
        if isinstance(raw_tip, TipSummary):
            return raw_tip
        if isinstance(raw_tip, dict):
            return TipSummary(**raw_tip)
        raise TypeError("Unsupported tip payload")

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

    @router.get(
        "/checkpoints/latest",
        response_model=TipSummary,
        responses={204: {"description": "No checkpoint available"}},
        summary="Fetch latest checkpoint tip",
    )
    async def get_latest_checkpoint() -> Response:
        tip = _normalize_tip(provider.tip())
        if tip is None:
            return Response(status_code=status.HTTP_204_NO_CONTENT)
        return JSONResponse(status_code=status.HTTP_200_OK, content=tip.model_dump(mode="json"))

    @router.get("/checkpoint/latest", include_in_schema=False)
    async def get_latest_checkpoint_legacy() -> Response:
        return await get_latest_checkpoint()

    @router.post(
        "/range_proof",
        response_model=RangeProofResponse,
        responses=ERROR_RESPONSES,
        summary="Request range proof from checkpoint height",
    )
    async def post_range_proof(request: Request) -> JSONResponse:
        with _start_span("federation.range_proof"):
            try:
                payload = await request.json()
            except Exception:
                return _error("invalid_json", status.HTTP_400_BAD_REQUEST, "Malformed JSON body")

            try:
                range_request = RangeProofRequest(**payload)
            except ValidationError:
                return _error("invalid_payload", status.HTTP_422_UNPROCESSABLE_ENTITY, "Invalid range proof payload")

            if range_request.max > range_limit:
                return _error(
                    "range_too_large",
                    status.HTTP_422_UNPROCESSABLE_ENTITY,
                    "Requested range exceeds limit",
                )

            entries = list(_normalize_entries(provider.range_slice(range_request.from_height, range_request.max)))
            tip = _normalize_tip(provider.tip())
            if tip is None:
                return _error("no_tip", status.HTTP_503_SERVICE_UNAVAILABLE, "No checkpoint tip available")

            response_model = build_range_response(
                entries,
                range_request,
                tip=tip,
                max_chunk_size=chunk_size,
            )
            size_bytes = _model_size_bytes(response_model)
            if size_bytes > chunk_bytes_limit:
                return _error(
                    "range_payload_too_large",
                    status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                    "Range proof payload exceeds configured limit",
                )

            peer_id = _peer_from_request(request)
            federation_metrics.add_range_bytes(peer_id, size_bytes)
            for chunk in response_model.chunks:
                federation_metrics.inc_range_chunk(peer_id, "ok")

            return JSONResponse(
                status_code=status.HTTP_200_OK,
                content=response_model.model_dump(mode="json", by_alias=True),
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

    @router.post(
        "/checkpoint",
        response_model=CheckpointResponse,
        responses=ERROR_RESPONSES,
        response_model_exclude_none=True,
        summary="Submit a PQC-signed checkpoint",
        openapi_extra={"requestBody": {"content": {"application/json": {"example": CHECKPOINT_REQUEST_EXAMPLE}}}},
    )
    async def submit_checkpoint(request: Request) -> JSONResponse:
        start_time = time.perf_counter()
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

        ts_utc = envelope.ts.astimezone(timezone.utc) if envelope.ts.tzinfo else envelope.ts.replace(tzinfo=timezone.utc)
        age_seconds = max(0.0, (datetime.now(timezone.utc) - ts_utc).total_seconds())
        latency_ms = max(0.0, (time.perf_counter() - start_time) * 1000.0)
        continuity_score = 1.0  # TODO: integrate real continuity metric in Phase 15-2.

        gradient = compute_gradient_score(
            verified=True,
            latency_ms=latency_ms,
            age_s=age_seconds,
            continuity=continuity_score,
        )
        trust = {"verified": True, "score": gradient}
        _register_success(peer.id)
        federation_metrics.set_last_sync(peer.id, age_seconds)
        federation_metrics.set_score(peer.id, gradient)
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "peer": peer.id,
                "trust": trust,
                "canonical_ts": envelope.canonical_ts(),
                "replayed": replayed,
            },
        )

    @router.post(
        "/verify",
        response_model=TrustPayload,
        responses=ERROR_RESPONSES,
        summary="Verify a checkpoint signature",
        openapi_extra={"requestBody": {"content": {"application/json": {"example": CHECKPOINT_REQUEST_EXAMPLE}}}},
    )
    async def verify_checkpoint(request: Request) -> JSONResponse:
        start_time = time.perf_counter()
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

        ts_utc = envelope.ts.astimezone(timezone.utc) if envelope.ts.tzinfo else envelope.ts.replace(tzinfo=timezone.utc)
        age_seconds = max(0.0, (datetime.now(timezone.utc) - ts_utc).total_seconds())
        latency_ms = max(0.0, (time.perf_counter() - start_time) * 1000.0)
        gradient = compute_gradient_score(
            verified=True,
            latency_ms=latency_ms,
            age_s=age_seconds,
            continuity=1.0,
        )
        trust = {"verified": True, "score": gradient}
        _register_success(peer_id)
        federation_metrics.set_last_sync(peer_id, age_seconds)
        federation_metrics.set_score(peer_id, gradient)
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={"verified": trust["verified"], "score": trust["score"]},
        )

    return router


__all__ = ["build_router"]
