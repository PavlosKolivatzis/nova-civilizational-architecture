"""Federation readiness and health helpers."""

from __future__ import annotations

import os
from time import time
from typing import Dict, List

from nova.federation.metrics import m


def _label_map(gauge, labels) -> Dict[str, str]:
    return dict(zip(gauge._labelnames, labels))  # type: ignore[attr-defined]


def get_peer_health() -> Dict[str, object]:
    """Return current federation metrics in a JSON-friendly form."""
    metrics = m()
    ready_gauge = metrics.get("ready")
    ready_value = ready_gauge._value.get() if ready_gauge else 0.0
    ready = ready_value >= 1.0

    height_gauge = metrics.get("height")
    height = int(height_gauge._value.get()) if height_gauge else 0

    # Ledger correlation
    ledger_info = {"height": 0, "head_age": 0.0, "gap": 0}
    try:
        from orchestrator.federation_poller import get_last_ledger

        ledger_info = get_last_ledger()
    except Exception:
        pass

    peer_up = metrics.get("peer_up")
    peer_last_seen = metrics.get("peer_last_seen")
    peer_quality = metrics.get("peer_quality")
    peer_p95 = metrics.get("peer_p95")
    peer_success = metrics.get("peer_success")
    peers: List[Dict[str, object]] = []
    if peer_up and getattr(peer_up, "_metrics", None):
        for labels in peer_up._metrics.keys():  # type: ignore[attr-defined]
            label_map = _label_map(peer_up, labels)
            peer_id = label_map.get("peer")
            if not peer_id:
                continue
            up_value = peer_up.labels(**label_map)._value.get()
            last_seen_value = 0.0
            if peer_last_seen:
                try:
                    last_seen_value = peer_last_seen.labels(**label_map)._value.get()
                except KeyError:
                    last_seen_value = 0.0
            quality_value = 0.0
            p95_value = 0.0
            success_rate_value = 0.0
            if peer_quality:
                try:
                    quality_value = peer_quality.labels(**label_map)._value.get()
                except KeyError:
                    quality_value = 0.0
            if peer_p95:
                try:
                    p95_value = peer_p95.labels(**label_map)._value.get()
                except KeyError:
                    p95_value = 0.0
            if peer_success:
                try:
                    success_rate_value = peer_success.labels(**label_map)._value.get()
                except KeyError:
                    success_rate_value = 0.0
            peers.append(
                {
                    "id": peer_id,
                    "state": "up" if up_value >= 1.0 else "unknown",
                    "last_seen": last_seen_value,
                    "quality": quality_value,
                    "success_rate": success_rate_value,
                    "p95": p95_value,
                }
            )

    remediation = {
        "reason": "none",
        "timestamp": 0.0,
        "interval": metrics.get("remediation_backoff", None)._value.get() if metrics.get("remediation_backoff") else 0.0,
        "context": {},
    }
    try:
        from orchestrator.federation_remediator import get_last_event

        remediation = get_last_event()
        if "interval" not in remediation:
            backoff_metric = metrics.get("remediation_backoff")
            remediation["interval"] = backoff_metric._value.get() if backoff_metric else 0.0
    except Exception:
        pass

    # Phase 16-2: Add peer sync status
    peer_sync_info = {
        "enabled": False,
        "peer_count": 0,
        "context": "solo",
        "novelty": 0.0,
    }
    try:
        from orchestrator.app import _peer_store
        from orchestrator import adaptive_wisdom_poller
        from nova.wisdom.generativity_context import ContextState

        sync_enabled = os.getenv("NOVA_FED_SYNC_ENABLED", "0") == "1"
        if sync_enabled and _peer_store:
            live_peers = _peer_store.get_live_peers(max_age_seconds=90)
            state = adaptive_wisdom_poller.get_state()

            # Get context state
            context_state = state.get("context", "solo")
            if hasattr(context_state, "value"):
                context_state = context_state.value

            peer_sync_info = {
                "enabled": True,
                "peer_count": len(live_peers),
                "context": context_state if isinstance(context_state, str) else "solo",
                "novelty": state.get("g_components", {}).get("novelty", 0.0),
            }
    except (ImportError, AttributeError):
        # Peer sync not available
        pass

    return {
        "ready": ready,
        "peers": peers,
        "checkpoint": {"height": height},
        "ledger": ledger_info,
        "remediation": remediation,
        "peer_sync": peer_sync_info,
    }


def is_ready(threshold_seconds: float = 120.0) -> bool:
    """Return True when federation is considered ready for traffic."""
    info = get_peer_health()
    if not info["ready"]:
        return False
    if not info["peers"]:
        return False
    last_success = m()["last_result_ts"].labels(status="success")._value.get()
    if not last_success:
        return False
    return (time() - last_success) < threshold_seconds
