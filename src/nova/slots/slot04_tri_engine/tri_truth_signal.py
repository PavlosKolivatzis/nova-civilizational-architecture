"""
TRI truth signal canonicalization utilities.

Provides:
- TriTruthSignal dataclass
- canonicalization helpers
- Semantic Mirror publishing shims
"""
from __future__ import annotations

from dataclasses import dataclass, asdict
from hashlib import blake2b
import json
import time
from typing import Any, Dict, Optional


def _clamp(value: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, value))


def _classify_band(coherence: float) -> str:
    if coherence >= 0.72:
        return "green"
    if coherence >= 0.5:
        return "amber"
    return "red"


@dataclass(frozen=True)
class TriTruthSignal:
    tri_coherence: float
    tri_drift_z: float
    tri_jitter: float
    tri_band: str
    canonical_hash: str
    anchor_id: str
    timestamp: float
    confidence: Optional[float] = None
    source_window: str = "live"

    def as_payload(self) -> Dict[str, Any]:
        payload = asdict(self)
        return payload


def _derive_drift(report: Dict[str, Any], coherence: float) -> float:
    raw = report.get("drift_z")
    if raw is None:
        baseline = float(report.get("tri_mean", coherence) or coherence)
        raw = 0.0 if baseline == 0 else (coherence - baseline) / 0.05
    try:
        drift = float(raw)
    except (TypeError, ValueError):
        drift = 0.0
    return _clamp(drift, -5.0, 5.0)


def _derive_jitter(report: Dict[str, Any], coherence: float) -> float:
    raw = report.get("phase_jitter")
    if raw is None:
        raw = max(0.0, 1.0 - coherence)
    try:
        jitter = float(raw)
    except (TypeError, ValueError):
        jitter = max(0.0, 1.0 - coherence)
    return _clamp(jitter, 0.0, 0.5)


def canonicalize_truth_signal(report: Dict[str, Any]) -> TriTruthSignal:
    """
    Build TriTruthSignal from raw TRI report.

    Args:
        report: Output from Slot04 TRI engines/adapters.
    """
    coherence = float(report.get("coherence") or report.get("tri_score") or 0.0)
    coherence = _clamp(coherence, 0.0, 1.0)
    drift = _derive_drift(report, coherence)
    jitter = _derive_jitter(report, coherence)
    band = _classify_band(coherence)
    timestamp = float(report.get("timestamp") or time.time())
    confidence = report.get("confidence")

    canonical_body = {
        "tri_coherence": round(coherence, 6),
        "tri_drift_z": round(drift, 4),
        "tri_jitter": round(jitter, 4),
        "tri_band": band,
        "timestamp": round(timestamp, 3),
        "confidence": round(float(confidence), 6) if isinstance(confidence, (int, float)) else None,
    }
    body_bytes = json.dumps(canonical_body, sort_keys=True, separators=(",", ":")).encode("utf-8")
    canonical_hash = blake2b(body_bytes, digest_size=32).hexdigest()
    anchor_id = f"tri::{canonical_hash[:16]}"

    return TriTruthSignal(
        tri_coherence=coherence,
        tri_drift_z=drift,
        tri_jitter=jitter,
        tri_band=band,
        canonical_hash=canonical_hash,
        anchor_id=anchor_id,
        timestamp=timestamp,
        confidence=confidence if isinstance(confidence, (int, float)) else None,
    )


def publish_to_semantic_mirror(signal: TriTruthSignal, ttl_seconds: int = 45) -> None:
    """Publish canonical signal to Semantic Mirror (best-effort)."""
    try:
        from orchestrator.semantic_mirror import get_semantic_mirror
    except Exception:
        return

    try:
        mirror = get_semantic_mirror()
    except Exception:
        return

    if mirror is None:
        return

    payload = signal.as_payload()
    try:
        mirror.set_context("slot04.tri_truth_signal", payload, ttl=ttl_seconds)
    except TypeError:
        try:
            mirror.set_context("slot04.tri_truth_signal", payload)
        except Exception:
            pass
    try:
        mirror.set_context("slot04.tri_canonized", signal.canonical_hash, ttl=ttl_seconds)
    except TypeError:
        try:
            mirror.set_context("slot04.tri_canonized", signal.canonical_hash)
        except Exception:
            pass


__all__ = [
    "TriTruthSignal",
    "canonicalize_truth_signal",
    "publish_to_semantic_mirror",
]
