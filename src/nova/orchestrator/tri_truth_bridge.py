"""
TRI Truth Bridge.

Canonicalizes Slot04 TRI reports, publishes to Semantic Mirror, and
optionally requests Slot01 attestation when NOVA_SLOT01_ROOT_MODE=1.
"""
from __future__ import annotations

import asyncio
import json
import os
import time
from typing import Any, Dict, Optional

from src_bootstrap import ensure_src_on_path

ensure_src_on_path()

from nova.slots.slot04_tri_engine.tri_truth_signal import (
    TriTruthSignal,
    canonicalize_truth_signal,
    publish_to_semantic_mirror,
)

_latest_signal: Optional[TriTruthSignal] = None
_bridge_metrics: Dict[str, Any] = {
    "last_hash": None,
    "last_attested_hash": None,
    "attest_events": 0,
    "attest_latency_ms_sum": 0.0,
    "attest_latency_samples": 0,
}
_slot1_initialized = False


async def _ensure_slot1_initialized():
    global _slot1_initialized
    if _slot1_initialized:
        return
    from nova.slots.slot01_truth_anchor import orchestrator_adapter as slot1

    await slot1.initialize({})
    _slot1_initialized = True


async def _register_anchor(signal: TriTruthSignal) -> None:
    await _ensure_slot1_initialized()
    from nova.slots.slot01_truth_anchor import orchestrator_adapter as slot1

    payload = {
        "op": "register",
        "anchor_id": signal.anchor_id,
        "value": json.dumps(signal.as_payload(), sort_keys=True, separators=(",", ":")),
        "metadata": {
            "source": "slot04_tri",
            "tri_band": signal.tri_band,
            "tri_drift_z": signal.tri_drift_z,
            "tri_jitter": signal.tri_jitter,
            "canonical_hash": signal.canonical_hash,
        },
    }
    request_id = f"tri-{signal.anchor_id}"
    await slot1.run(payload, request_id=request_id)


def _attest_if_required(signal: TriTruthSignal) -> None:
    if os.getenv("NOVA_SLOT01_ROOT_MODE", "0").strip() != "1":
        return

    if _bridge_metrics.get("last_attested_hash") == signal.canonical_hash:
        return

    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None

    async def _call():
        await _register_anchor(signal)

    start = time.perf_counter()
    if loop and loop.is_running():
        loop.create_task(_call())
        latency_ms = None
    else:
        asyncio.run(_call())
        latency_ms = (time.perf_counter() - start) * 1000.0

    _bridge_metrics["last_attested_hash"] = signal.canonical_hash
    _bridge_metrics["attest_events"] += 1
    if latency_ms is not None:
        _bridge_metrics["attest_latency_ms_sum"] += latency_ms
        _bridge_metrics["attest_latency_samples"] += 1


def process_tri_truth_signal(report: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Canonicalize TRI report, publish to Semantic Mirror, and trigger attestation.
    Returns the canonical payload (dict) or None if canonicalization failed.
    """
    global _latest_signal
    try:
        signal = canonicalize_truth_signal(report)
    except Exception:
        return None

    _latest_signal = signal
    _bridge_metrics["last_hash"] = signal.canonical_hash

    try:
        publish_to_semantic_mirror(signal)
    except Exception:
        pass

    try:
        _attest_if_required(signal)
    except Exception:
        # Attestation errors should not break TRI processing
        pass

    return signal.as_payload()


def get_bridge_metrics() -> Dict[str, Any]:
    """Snapshot of latest TRI bridge metrics for Prometheus exporter."""
    payload: Dict[str, Any] = {
        "tri_coherence": _latest_signal.tri_coherence if _latest_signal else None,
        "canonical_hash": _bridge_metrics.get("last_hash"),
        "attest_events": _bridge_metrics.get("attest_events", 0),
    }
    samples = _bridge_metrics.get("attest_latency_samples", 0)
    if samples:
        payload["attest_latency_ms_avg"] = (
            _bridge_metrics.get("attest_latency_ms_sum", 0.0) / samples
        )
    else:
        payload["attest_latency_ms_avg"] = 0.0
    return payload


__all__ = ["process_tri_truth_signal", "get_bridge_metrics"]
