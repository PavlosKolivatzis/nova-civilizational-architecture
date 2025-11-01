"""Federation metrics background poller."""

import os
import threading
import time
import time as _t
from contextlib import contextmanager

from nova.federation.metrics import m

from .federation_client import get_peer_list, get_verified_checkpoint


def _float_env(name: str, default: float) -> float:
    try:
        return float(os.getenv(name, default))
    except Exception:
        return default


INTERVAL = _float_env("NOVA_FED_SCRAPE_INTERVAL", 15.0)
TIMEOUT = _float_env("NOVA_FED_SCRAPE_TIMEOUT", 2.0)

_stop = threading.Event()
_thread: threading.Thread | None = None
_lock = threading.Lock()
_known_peers: set[str] = set()


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
                for peer in peers:
                    peer_id = getattr(peer, "id", str(peer))
                    peer_up.labels(peer=peer_id).set(1.0)
                    current_peer_ids.append(peer_id)
                global _known_peers
                stale_peers = _known_peers - set(current_peer_ids)
                for peer_id in stale_peers:
                    peer_up.labels(peer=peer_id).set(0.0)
                _known_peers = set(current_peer_ids)
                metrics["peers"].set(len(peers))
                metrics["height"].set(checkpoint.get("height", 0))
                metrics["last_ts"].set(time.time())
                metrics["pull_result"].labels(status="success").inc()
            except Exception:
                metrics["pull_result"].labels(status="error").inc()
        _stop.wait(INTERVAL)
