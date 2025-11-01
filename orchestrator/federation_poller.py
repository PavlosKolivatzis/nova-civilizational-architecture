"""Federation metrics background poller."""

import os
import threading
import time
import time as _t
from contextlib import contextmanager
from typing import Optional, Set

from nova.federation.metrics import m

from .federation_client import get_peer_list, get_verified_checkpoint


def _get_interval() -> float:
    raw = os.getenv("NOVA_FED_SCRAPE_INTERVAL", "")
    try:
        return float(raw) if raw else 15.0
    except Exception:
        return 15.0


def _get_timeout() -> float:
    raw = os.getenv("NOVA_FED_SCRAPE_TIMEOUT", "")
    try:
        return float(raw) if raw else 2.0
    except Exception:
        return 2.0


INTERVAL = _get_interval()
TIMEOUT = _get_timeout()

_stop = threading.Event()
_thread: Optional[threading.Thread] = None
_lock = threading.Lock()
_known_peers: Set[str] = set()


@contextmanager
def _timed(summary):
    start = _t.perf_counter()
    try:
        yield
    finally:
        summary.observe(_t.perf_counter() - start)


def start():
    global _thread
    with _lock:
        if _thread and _thread.is_alive():
            return _thread
        _stop.clear()
        _thread = threading.Thread(target=_loop, name="federation-metrics", daemon=True)
        _thread.start()
        return _thread


def stop() -> None:
    global _thread, _known_peers
    _stop.set()
    with _lock:
        thread = _thread
        _thread = None
        _known_peers.clear()
    if thread and thread.is_alive():
        thread.join(timeout=1.0)


def _loop():
    metrics = m()
    while not _stop.is_set():
        with _timed(metrics["pull_seconds"]):
            try:
                peers = get_peer_list(timeout=TIMEOUT) or []
                checkpoint = get_verified_checkpoint(timeout=TIMEOUT) or {"height": 0}
                current_peer_ids = []
                peer_up = metrics["peer_up"]
                peer_last_seen = metrics["peer_last_seen"]
                now = time.time()
                for peer in peers:
                    peer_id = getattr(peer, "id", str(peer))
                    peer_up.labels(peer=peer_id).set(1.0)
                    peer_last_seen.labels(peer=peer_id).set(now)
                    current_peer_ids.append(peer_id)
                global _known_peers
                stale_peers = _known_peers - set(current_peer_ids)
                for peer_id in stale_peers:
                    peer_up.labels(peer=peer_id).set(0.0)
                    peer_last_seen.labels(peer=peer_id).set(0.0)
                _known_peers = set(current_peer_ids)
                metrics["peers"].set(len(peers))
                metrics["height"].set(checkpoint.get("height", 0))
                metrics["last_result_ts"].labels(status="success").set(now)
                metrics["pull_result"].labels(status="success").inc()
                metrics["ready"].set(1.0 if len(peers) > 0 else 0.0)
            except Exception:
                now = time.time()
                metrics["last_result_ts"].labels(status="error").set(now)
                metrics["pull_result"].labels(status="error").inc()
                metrics["ready"].set(0.0)
        _stop.wait(INTERVAL)
