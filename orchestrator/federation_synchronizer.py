"""
Federation Peer Synchronizer (Phase 16-2).

Pull-based peer synchronization for live Novelty (N) calculation.
Pulls /federation/sync/summary from configured peers, validates schema,
and maintains an in-memory PeerStore with rolling 5-minute windows.

Design:
- Thread-safe PeerStore with deque-based rolling windows
- Background task with configurable interval and timeout
- Metrics: pull latency, errors, peer last_seen timestamps
- Graceful degradation on peer unavailability
"""

from __future__ import annotations

import asyncio
import logging
import os
import threading
import time
from collections import deque
from dataclasses import dataclass
from typing import Dict, List, Optional

try:
    import httpx
    HTTPX_AVAILABLE = True
except ImportError:
    HTTPX_AVAILABLE = False

from pydantic import BaseModel, ValidationError

__all__ = ["PeerStore", "PeerSync", "PeerSample"]


# -------------------------------------------------------------------------
# Schema
# -------------------------------------------------------------------------

class PeerMetrics(BaseModel):
    """Peer metrics payload from /federation/sync/summary."""
    peer_quality: float
    stability_margin: float
    hopf_distance: float
    spectral_radius: float
    gamma: float
    g_components: Dict[str, float]
    g_star: float


class PeerSyncPayload(BaseModel):
    """Full payload from /federation/sync/summary endpoint."""
    node_id: str
    ts: float
    version: str
    metrics: PeerMetrics
    sig: Optional[str] = None  # Placeholder for Phase 16-4 PQC signatures


@dataclass
class PeerSample:
    """Single peer sample with timestamp and metrics."""
    peer_id: str
    ts: float
    last_seen: float
    peer_quality: float
    stability_margin: float
    hopf_distance: float
    spectral_radius: float
    gamma: float
    g_star: float
    g_components: Dict[str, float]

    @property
    def generativity(self) -> float:
        """Alias for g_star to match compute_novelty() interface."""
        return self.g_star


# -------------------------------------------------------------------------
# PeerStore
# -------------------------------------------------------------------------

class PeerStore:
    """
    Thread-safe in-memory store for peer samples.

    Maintains rolling 5-minute windows per peer for time-series analysis.
    """

    def __init__(self, window_seconds: int = 300):
        """
        Initialize peer store.

        Args:
            window_seconds: Rolling window size in seconds (default: 5 minutes)
        """
        self._lock = threading.RLock()
        self._peers: Dict[str, deque] = {}  # peer_id -> deque[PeerSample]
        self._window_seconds = window_seconds
        self._logger = logging.getLogger(__name__)

    def update(self, sample: PeerSample) -> None:
        """
        Add or update a peer sample.

        Args:
            sample: PeerSample to add to the store
        """
        with self._lock:
            if sample.peer_id not in self._peers:
                self._peers[sample.peer_id] = deque()

            # Add new sample
            self._peers[sample.peer_id].append(sample)

            # Prune old samples outside window
            cutoff = time.time() - self._window_seconds
            while (self._peers[sample.peer_id] and
                   self._peers[sample.peer_id][0].ts < cutoff):
                self._peers[sample.peer_id].popleft()

    def get_live_peers(self, max_age_seconds: int = 90) -> List[PeerSample]:
        """
        Get list of live peers (recent samples).

        Args:
            max_age_seconds: Maximum age for "live" peers (default: 90s)

        Returns:
            List of PeerSample objects with recent last_seen timestamps
        """
        with self._lock:
            now = time.time()
            cutoff = now - max_age_seconds
            live_peers = []

            for peer_id, samples in self._peers.items():
                if samples and samples[-1].last_seen >= cutoff:
                    live_peers.append(samples[-1])

            return live_peers

    def get_peer_count(self, max_age_seconds: int = 90) -> int:
        """Get count of live peers."""
        return len(self.get_live_peers(max_age_seconds))

    def get_peer_gstars(self, max_age_seconds: int = 90) -> List[float]:
        """Get g_star values from live peers for novelty calculation."""
        live_peers = self.get_live_peers(max_age_seconds)
        return [p.g_star for p in live_peers]

    def clear(self) -> None:
        """Clear all peer data (for testing)."""
        with self._lock:
            self._peers.clear()


# -------------------------------------------------------------------------
# PeerSync
# -------------------------------------------------------------------------

class PeerSync:
    """
    Background task for pulling peer metrics.

    Polls configured peers at regular intervals, validates payloads,
    and updates PeerStore with fresh samples.
    """

    def __init__(self, peer_store: PeerStore):
        """
        Initialize peer synchronizer.

        Args:
            peer_store: PeerStore instance to populate
        """
        self.peer_store = peer_store
        self._logger = logging.getLogger(__name__)
        self._task: Optional[asyncio.Task] = None
        self._running = False

        # Configuration from environment
        self._enabled = os.getenv("NOVA_FED_SYNC_ENABLED", "0") == "1"
        self._peers = self._parse_peers(os.getenv("NOVA_FED_PEERS", ""))
        self._interval = float(os.getenv("NOVA_FED_SYNC_INTERVAL", "30"))
        self._timeout = float(os.getenv("NOVA_FED_SYNC_TIMEOUT", "2.5"))

    def _parse_peers(self, peers_str: str) -> List[str]:
        """Parse comma-separated peer URLs."""
        if not peers_str:
            return []
        return [p.strip() for p in peers_str.split(",") if p.strip()]

    async def _fetch_peer(self, peer_url: str, client: httpx.AsyncClient) -> Optional[PeerSample]:
        """
        Fetch metrics from a single peer.

        Args:
            peer_url: Base URL of peer (e.g., http://10.0.0.11:8100)
            client: httpx AsyncClient for HTTP requests

        Returns:
            PeerSample if successful, None on error
        """
        endpoint = f"{peer_url}/federation/sync/summary"

        try:
            start = time.time()
            response = await client.get(endpoint, timeout=self._timeout)
            duration = time.time() - start

            response.raise_for_status()

            # Parse and validate payload
            data = response.json()
            payload = PeerSyncPayload(**data)

            # Convert to PeerSample
            sample = PeerSample(
                peer_id=payload.node_id,
                ts=payload.ts,
                last_seen=time.time(),
                peer_quality=payload.metrics.peer_quality,
                stability_margin=payload.metrics.stability_margin,
                hopf_distance=payload.metrics.hopf_distance,
                spectral_radius=payload.metrics.spectral_radius,
                gamma=payload.metrics.gamma,
                g_star=payload.metrics.g_star,
                g_components=payload.metrics.g_components,
            )

            # Emit metrics
            self._logger.debug(
                f"Synced peer {payload.node_id} from {peer_url} "
                f"(g*={payload.metrics.g_star:.3f}, latency={duration:.3f}s)"
            )

            # Phase 16-2: Record prometheus metrics
            try:
                from orchestrator.prometheus_metrics import (
                    federation_sync_latency_histogram,
                    federation_peer_last_seen_gauge,
                )
                federation_sync_latency_histogram.observe(duration)
                federation_peer_last_seen_gauge.labels(peer_id=payload.node_id).set(sample.last_seen)
            except ImportError:
                # Prometheus metrics not available
                pass

            return sample

        except httpx.HTTPError as e:
            self._logger.warning(f"HTTP error fetching {endpoint}: {e}")
            # Record error metric
            try:
                from orchestrator.prometheus_metrics import federation_sync_errors_counter
                # Extract peer_id from URL for labeling (use hostname)
                peer_id = peer_url.replace("http://", "").replace("https://", "").split(":")[0]
                federation_sync_errors_counter.labels(peer_id=peer_id, error_type="http_error").inc()
            except ImportError:
                pass
            return None
        except ValidationError as e:
            self._logger.warning(f"Schema validation error for {endpoint}: {e}")
            # Record error metric
            try:
                from orchestrator.prometheus_metrics import federation_sync_errors_counter
                peer_id = peer_url.replace("http://", "").replace("https://", "").split(":")[0]
                federation_sync_errors_counter.labels(peer_id=peer_id, error_type="validation_error").inc()
            except ImportError:
                pass
            return None
        except Exception as e:
            self._logger.error(f"Unexpected error fetching {endpoint}: {e}")
            # Record error metric
            try:
                from orchestrator.prometheus_metrics import federation_sync_errors_counter
                peer_id = peer_url.replace("http://", "").replace("https://", "").split(":")[0]
                federation_sync_errors_counter.labels(peer_id=peer_id, error_type="unexpected_error").inc()
            except ImportError:
                pass
            return None

    async def _sync_loop(self) -> None:
        """Main sync loop."""
        if not HTTPX_AVAILABLE:
            self._logger.warning("httpx not available, peer sync disabled")
            return

        self._logger.info(
            f"Starting peer sync: {len(self._peers)} peers, "
            f"interval={self._interval}s, timeout={self._timeout}s"
        )

        async with httpx.AsyncClient() as client:
            while self._running:
                for peer_url in self._peers:
                    if not self._running:
                        break

                    sample = await self._fetch_peer(peer_url, client)
                    if sample:
                        self.peer_store.update(sample)

                # Wait for next interval
                await asyncio.sleep(self._interval)

    def start(self) -> None:
        """Start the peer sync background task."""
        if not self._enabled:
            self._logger.info("Peer sync disabled (NOVA_FED_SYNC_ENABLED=0)")
            return

        if not self._peers:
            self._logger.info("No peers configured (NOVA_FED_PEERS empty)")
            return

        if self._running:
            self._logger.warning("Peer sync already running")
            return

        self._running = True

        # Create task in event loop
        loop = asyncio.get_event_loop()
        self._task = loop.create_task(self._sync_loop())
        self._logger.info("Peer sync started")

    def stop(self) -> None:
        """Stop the peer sync background task."""
        if not self._running:
            return

        self._running = False

        if self._task:
            self._task.cancel()
            self._task = None

        self._logger.info("Peer sync stopped")
