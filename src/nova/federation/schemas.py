"""Pydantic schemas for federation envelopes and canonical payloads."""

from __future__ import annotations

import base64
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Literal, Optional, Sequence
from uuid import UUID

from pydantic import AnyHttpUrl, BaseModel, Field, field_validator


class Peer(BaseModel):
    """Static peer registry entry."""

    id: str
    url: AnyHttpUrl
    pubkey_path: Path
    weight: float = Field(1.0, ge=0.0)
    enabled: bool = True

    @field_validator("pubkey_path", mode="before")
    def _coerce_path(cls, value: Any) -> Path:
        return Path(value)


class CheckpointEnvelope(BaseModel):
    """Canonical checkpoint payload signed by peers."""

    anchor_id: UUID
    merkle_root: str
    height: int = Field(..., ge=0)
    ts: datetime
    algo: Literal["sha3-256"] = "sha3-256"
    sig_b64: str = Field(..., min_length=800, max_length=4000)
    producer: str
    version: Literal["v1"] = "v1"

    @field_validator("merkle_root")
    def _validate_merkle_root(cls, value: str) -> str:
        if len(value) != 64:
            raise ValueError("merkle_root must be 64 hex characters")
        if not all(ch in "0123456789abcdefABCDEF" for ch in value):
            raise ValueError("merkle_root must be hexadecimal")
        return value.lower()

    @field_validator("sig_b64")
    def _validate_sig(cls, value: str) -> str:
        try:
            base64.b64decode(value, validate=True)
        except Exception as exc:  # pragma: no cover - invalid base64
            raise ValueError("sig_b64 must be valid base64") from exc
        return value

    def canonical_ts(self) -> str:
        """Return timestamp normalized to UTC Z with seconds precision."""
        if self.ts.tzinfo is None:
            dt = self.ts.replace(tzinfo=timezone.utc)
        else:
            dt = self.ts.astimezone(timezone.utc)
        return dt.replace(microsecond=0).isoformat().replace("+00:00", "Z")

    def canonical_json(self) -> str:
        """Return canonical JSON (ASCII, sorted keys, no whitespace)."""
        payload = {
            "algo": self.algo,
            "anchor_id": str(self.anchor_id),
            "height": self.height,
            "merkle_root": self.merkle_root,
            "producer": self.producer,
            "sig_b64": self.sig_b64,
            "ts": self.canonical_ts(),
            "version": self.version,
        }
        return json.dumps(payload, ensure_ascii=True, separators=(",", ":"), sort_keys=True)

    def canonical_bytes(self) -> bytes:
        return self.canonical_json().encode("ascii")

class RangeProofRequest(BaseModel):
    """Request payload for range proofs."""

    from_height: int = Field(..., ge=0)
    max: int = Field(256, ge=1, le=2048)


class ProofChunk(BaseModel):
    """Chunk of consecutive checkpoint roots with Merkle proof."""

    start: int = Field(..., ge=0)
    end: int = Field(..., ge=0)
    roots: List[str] = Field(default_factory=list)
    proof: List[str] = Field(default_factory=list)

    @field_validator("roots", mode="after")
    def _validate_roots(cls, values: Sequence[str]) -> List[str]:
        normalized: List[str] = []
        for value in values:
            value_lower = value.lower()
            if len(value_lower) != 64 or not all(ch in "0123456789abcdef" for ch in value_lower):
                raise ValueError("roots must be 64-character lowercase hex strings")
            normalized.append(value_lower)
        return normalized

    @field_validator("proof", mode="after")
    def _validate_proof(cls, values: Sequence[str]) -> List[str]:
        normalized: List[str] = []
        for value in values:
            value_lower = value.lower()
            if len(value_lower) != 64 or not all(ch in "0123456789abcdef" for ch in value_lower):
                raise ValueError("proof hashes must be 64-character lowercase hex strings")
            normalized.append(value_lower)
        return normalized


class TipSummary(BaseModel):
    height: int = Field(..., ge=0)
    merkle_root: str = Field(..., min_length=64, max_length=64)
    ts: datetime
    producer: str


class RangeProofResponse(BaseModel):
    """Response containing range proof chunks and tip summary."""

    chunks: List[ProofChunk]
    tip: TipSummary


class ContinuityReceipt(BaseModel):
    """Receipt recording a verified range or divergence event."""

    peer: str
    range_start: int = Field(..., ge=0)
    range_end: int = Field(..., ge=0)
    tip_height: int = Field(..., ge=0)
    tip_root: str = Field(..., min_length=64, max_length=64)
    status: Literal["ok", "divergence"]
    ts: datetime
    details: Dict[str, Any] = Field(default_factory=dict)


class PeerManifestKey(BaseModel):
    """Key descriptor published by a peer."""

    kty: Literal["pq_dilithium2"]
    kid: str
    pub: str
    activated_at: datetime = Field(alias="from")
    expires_at: Optional[datetime] = None


class PeerManifest(BaseModel):
    """Signed manifest describing peer endpoint and active keys."""

    id: str
    endpoint: AnyHttpUrl
    keys: List[PeerManifestKey]
    sig: str
    version: Literal["v1"] = "v1"
    issued_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    @field_validator("keys", mode="after")
    def _require_keys(cls, values: Sequence[PeerManifestKey]) -> List[PeerManifestKey]:
        if not values:
            raise ValueError("keys list must not be empty")
        return list(values)


class KeyRotationReceipt(BaseModel):
    """Receipt acknowledging manifest rotation for a peer."""

    peer: str
    key_id: str
    activated_at: datetime
    ts: datetime
    manifest_version: str
    details: Dict[str, Any] = Field(default_factory=dict)


__all__ = [
    "Peer",
    "CheckpointEnvelope",
    "RangeProofRequest",
    "ProofChunk",
    "RangeProofResponse",
    "TipSummary",
    "ContinuityReceipt",
    "PeerManifest",
    "PeerManifestKey",
    "KeyRotationReceipt",
]
