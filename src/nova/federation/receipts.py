"""Receipt builders for federation events."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, Optional

from nova.federation.schemas import (
    ContinuityReceipt,
    KeyRotationReceipt,
    PeerManifest,
    TipSummary,
)


def _now() -> datetime:
    return datetime.now(timezone.utc)


def build_continuity_receipt(
    peer_id: str,
    *,
    range_start: int,
    range_end: int,
    tip: TipSummary,
    status: str,
    details: Optional[Dict[str, Any]] = None,
) -> ContinuityReceipt:
    detail_payload = details or {}
    return ContinuityReceipt(
        peer=peer_id,
        range_start=range_start,
        range_end=range_end,
        tip_height=tip.height,
        tip_root=tip.merkle_root,
        status="ok" if status == "ok" else "divergence",
        ts=_now(),
        details=detail_payload,
    )


def build_divergence_receipt(
    peer_id: str,
    *,
    divergence_height: int,
    expected_root: str,
    observed_root: str,
    tip: TipSummary,
) -> ContinuityReceipt:
    return build_continuity_receipt(
        peer_id,
        range_start=divergence_height,
        range_end=divergence_height,
        tip=tip,
        status="divergence",
        details={
            "expected_root": expected_root,
            "observed_root": observed_root,
        },
    )


def build_key_rotation_receipt(peer_id: str, manifest: PeerManifest) -> KeyRotationReceipt:
    latest = manifest.keys[-1]
    return KeyRotationReceipt(
        peer=peer_id,
        key_id=latest.kid,
        activated_at=latest.activated_at,
        ts=_now(),
        manifest_version=manifest.version,
        details={
            "endpoint": str(manifest.endpoint),
        },
    )


__all__ = [
    "build_continuity_receipt",
    "build_divergence_receipt",
    "build_key_rotation_receipt",
]
