"""Pydantic schemas for federation envelopes and canonical payloads."""

from __future__ import annotations

import base64
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Literal, Optional
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


__all__ = ["Peer", "CheckpointEnvelope"]
