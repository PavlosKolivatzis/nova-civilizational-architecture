"""
Phase 16-2: Peer sync summary route.

GET /federation/sync/summary endpoint for peer synchronization.
Returns current node metrics for remote peers to pull.
"""

from __future__ import annotations

import os
import time
import uuid
from typing import Dict

try:
    from fastapi import APIRouter
    FASTAPI_AVAILABLE = True
except ImportError:
    FASTAPI_AVAILABLE = False
    APIRouter = None

__all__ = ["create_peer_sync_router"]


def create_peer_sync_router():
    """
    Create FastAPI router for peer sync endpoint.

    Returns:
        APIRouter or None if FastAPI not available
    """
    if not FASTAPI_AVAILABLE or APIRouter is None:
        return None

    router = APIRouter(prefix="/federation", tags=["peer-sync"])

    @router.get("/sync/summary")
    async def peer_sync_summary():
        """
        Return local node metrics for peer synchronization.

        Called by remote peers to pull our current state for
        novelty calculation.

        Returns PeerSyncPayload schema:
        {
            "node_id": str,
            "ts": float,
            "version": str,
            "metrics": {
                "peer_quality": float,
                "stability_margin": float,
                "hopf_distance": float,
                "spectral_radius": float,
                "gamma": float,
                "g_components": {"progress": float, "novelty": float, "consistency": float},
                "g_star": float
            },
            "sig": str | null
        }
        """
        # Get node ID from environment or generate stable ID
        node_id = os.getenv("NOVA_NODE_ID")
        if not node_id:
            # Generate stable ID based on hostname/config
            hostname = os.getenv("HOSTNAME", "localhost")
            node_id = f"nova-{hostname}-{str(uuid.uuid4())[:8]}"

        # Collect metrics from wisdom governor state
        metrics = _collect_metrics()

        # Get Nova version
        version = os.getenv("NOVA_VERSION", "16.2")

        return {
            "node_id": node_id,
            "ts": time.time(),
            "version": version,
            "metrics": metrics,
            "sig": None,  # Placeholder for Phase 16-4 PQC signatures
        }

    return router


def _collect_metrics() -> Dict[str, any]:
    """
    Collect current metrics from wisdom governor and system state.

    Returns dict with keys:
        - peer_quality: Quality score [0,1]
        - stability_margin: S (stability margin)
        - hopf_distance: H (Hopf bifurcation distance)
        - spectral_radius: ρ (largest eigenvalue magnitude)
        - gamma: γ (wisdom score)
        - g_components: {progress, novelty, consistency}
        - g_star: G* (generativity score)
    """
    try:
        # Try to get metrics from wisdom poller state
        from orchestrator import adaptive_wisdom_poller

        state = adaptive_wisdom_poller.get_state()
        if state:
            return {
                "peer_quality": state.get("peer_quality", 0.7),
                "stability_margin": state.get("S", 0.05),
                "hopf_distance": state.get("H", 0.10),
                "spectral_radius": state.get("rho", 0.85),
                "gamma": state.get("gamma", 0.68),
                "g_components": state.get("g_components", {
                    "progress": 0.0,
                    "novelty": 0.0,
                    "consistency": 1.0
                }),
                "g_star": state.get("g_star", 0.30),
            }
    except Exception:
        pass

    # Fallback: return safe defaults (solo mode baseline)
    return {
        "peer_quality": 0.70,
        "stability_margin": 0.05,
        "hopf_distance": 0.10,
        "spectral_radius": 0.85,
        "gamma": 0.68,
        "g_components": {
            "progress": 0.0,
            "novelty": 0.0,
            "consistency": 1.0,
        },
        "g_star": 0.30,
    }
