"""Federation metrics background poller."""

import math
import os
import threading
import time
import time as _t
from collections import deque
from contextlib import contextmanager
from typing import Deque, Dict, Optional, Set, Tuple

from nova.federation.metrics import m

from .federation_client import get_peer_metrics


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
_BASE_INTERVAL = INTERVAL
_MIN_INTERVAL = max(1.0, INTERVAL)
_MAX_INTERVAL = float(os.getenv("NOVA_FED_SCRAPE_MAX_INTERVAL", str(max(_MIN_INTERVAL * 8, _MIN_INTERVAL))))
if _MAX_INTERVAL < _MIN_INTERVAL:
    _MAX_INTERVAL = _MIN_INTERVAL
_CURRENT_INTERVAL = INTERVAL
_EMPTY_PEERS_STREAK = 0
_LAST_EMPTY_PEERS_SIGNAL = 0.0

_NO_PEERS_THRESHOLD_RAW = os.getenv("NOVA_FEDERATION_NO_PEER_THRESHOLD", "5")
try:
    NO_PEERS_THRESHOLD = int(_NO_PEERS_THRESHOLD_RAW)
except Exception:
    NO_PEERS_THRESHOLD = 5

_NO_PEERS_COOLDOWN_RAW = os.getenv("NOVA_FEDERATION_NO_PEER_COOLDOWN", "600")
try:
    NO_PEERS_COOLDOWN = int(_NO_PEERS_COOLDOWN_RAW)
except Exception:
    NO_PEERS_COOLDOWN = 600

_QUALITY_WINDOW = 20
_PEER_WINDOWS: Dict[str, Dict[str, Deque[float]]] = {}
_PEER_LAST_SUCCESS_TS: Dict[str, float] = {}


def _quality_params() -> Tuple[float, float, float, float, float]:
    raw_w1 = os.getenv("NOVA_FED_QUALITY_W1", "")
    raw_w2 = os.getenv("NOVA_FED_QUALITY_W2", "")
    raw_w3 = os.getenv("NOVA_FED_QUALITY_W3", "")

    try:
        w1 = float(raw_w1) if raw_w1.strip() else 0.5
    except Exception:
        w1 = 0.5
    try:
        w2 = float(raw_w2) if raw_w2.strip() else 0.3
    except Exception:
        w2 = 0.3
    try:
        w3 = float(raw_w3) if raw_w3.strip() else 0.2
    except Exception:
        w3 = 0.2

    total = w1 + w2 + w3
    if total <= 0:
        w1, w2, w3 = 0.5, 0.3, 0.2
        total = 1.0
    w1, w2, w3 = (w1 / total, w2 / total, w3 / total)

    raw_lat_cap = os.getenv("NOVA_FED_QUALITY_LAT_CAP_SEC", "")
    try:
        lat_cap = float(raw_lat_cap) if raw_lat_cap.strip() else 2.0
    except Exception:
        lat_cap = 2.0
    lat_cap = max(lat_cap, 1e-6)

    raw_tau = os.getenv("NOVA_FED_QUALITY_TAU_SEC", "")
    try:
        tau = float(raw_tau) if raw_tau.strip() else 300.0
    except Exception:
        tau = 300.0
    tau = max(tau, 1e-6)

    return w1, w2, w3, lat_cap, tau


def _quality_gate_config() -> Optional[Tuple[float, int]]:
    threshold_raw = os.getenv("NOVA_FED_MIN_PEER_QUALITY", "").strip()
    if not threshold_raw:
        return None
    try:
        threshold = float(threshold_raw)
    except Exception:
        return None
    min_peers_raw = os.getenv("NOVA_FED_MIN_GOOD_PEERS", "").strip()
    try:
        min_good = int(min_peers_raw) if min_peers_raw else 1
    except Exception:
        min_good = 1
    return threshold, max(min_good, 1)


def _peer_window(peer_id: str) -> Dict[str, Deque[float]]:
    window = _PEER_WINDOWS.get(peer_id)
    if window is None:
        window = {
            "durations": deque(maxlen=_QUALITY_WINDOW),
            "success": deque(maxlen=_QUALITY_WINDOW),
        }
        _PEER_WINDOWS[peer_id] = window
    return window


def _percentile(values, percentile: float) -> float:
    if not values:
        return 0.0
    sorted_values = sorted(values)
    idx = max(
        0,
        min(len(sorted_values) - 1, int(math.ceil(percentile * len(sorted_values)) - 1)),
    )
    return sorted_values[idx]


def _compute_quality(
    successes: Deque[float],
    durations: Deque[float],
    last_success_ts: float,
    now: float,
    params: Tuple[float, float, float, float, float],
) -> Tuple[float, float, float, float]:
    w1, w2, w3, lat_cap, tau = params
    success_rate = sum(successes) / len(successes) if successes else 0.0
    if durations:
        p95 = _percentile(list(durations), 0.95)
        lat_score = max(0.0, min(1.0, 1.0 - (p95 / lat_cap)))
    else:
        p95 = 0.0
        lat_score = 0.0
    freshness = 0.0
    if last_success_ts:
        freshness = math.exp(-max(0.0, now - last_success_ts) / tau)
    quality = max(0.0, min(1.0, w1 * success_rate + w2 * lat_score + w3 * freshness))
    return quality, success_rate, p95, freshness


def _update_quality_metrics(metrics_map: Dict[str, object], params: Tuple[float, float, float, float, float]) -> Dict[str, float]:
    now = time.time()
    quality_scores: Dict[str, float] = {}
    for peer_id, window in _PEER_WINDOWS.items():
        quality, success_rate, p95, _ = _compute_quality(
            window["success"],
            window["durations"],
            _PEER_LAST_SUCCESS_TS.get(peer_id, 0.0),
            now,
            params,
        )
        metrics_map["peer_quality"].labels(peer=peer_id).set(quality)
        metrics_map["peer_p95"].labels(peer=peer_id).set(p95)
        metrics_map["peer_success"].labels(peer=peer_id).set(success_rate)
        quality_scores[peer_id] = quality
    return quality_scores


def _apply_quality_gate(base_ready: bool, quality_scores: Dict[str, float], metrics_map: Dict[str, object]) -> bool:
    gate = _quality_gate_config()
    ready = base_ready
    if gate:
        threshold, min_good = gate
        good_peers = sum(1 for score in quality_scores.values() if score >= threshold)
        if good_peers < min_good:
            ready = False
    metrics_map["ready"].set(1.0 if ready else 0.0)
    return ready


def reset_peer_quality_state() -> None:
    """Testing helper to clear peer quality rolling state."""
    _PEER_WINDOWS.clear()
    _PEER_LAST_SUCCESS_TS.clear()

_stop = threading.Event()
_thread: Optional[threading.Thread] = None
_lock = threading.Lock()
_known_peers: Set[str] = set()


def get_interval() -> float:
    with _lock:
        return _CURRENT_INTERVAL


def get_base_interval() -> float:
    return _BASE_INTERVAL


def set_interval(seconds: float) -> float:
    global _CURRENT_INTERVAL
    bounded = max(_MIN_INTERVAL, min(seconds, _MAX_INTERVAL))
    with _lock:
        _CURRENT_INTERVAL = bounded
    try:
        m()["remediation_backoff"].set(bounded)
    except Exception:
        pass
    return bounded


def reset_interval() -> None:
    set_interval(_BASE_INTERVAL)


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
    try:
        m()["remediation_backoff"].set(get_interval())
    except Exception:
        pass
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
    reset_interval()


def _loop():
    metrics = m()
    while not _stop.is_set():
        with _timed(metrics["pull_seconds"]):
            params = _quality_params()
            peer_ids: list[str] = []
            success_timestamp: float | None = None
            try:
                peers, checkpoint, peer_stats = get_peer_metrics(timeout=TIMEOUT)
                peer_ids = [getattr(peer, "id", str(peer)) for peer in peers]
                _update_empty_peers(peer_ids, metrics)
                peer_up = metrics["peer_up"]
                peer_last_seen = metrics["peer_last_seen"]
                now = time.time()
                for peer in peers:
                    peer_id = getattr(peer, "id", str(peer))
                    stats = peer_stats.get(peer_id, {})
                    success = bool(stats.get("success"))
                    duration = float(stats.get("duration", 0.0))
                    window = _peer_window(peer_id)
                    window["durations"].append(duration)
                    window["success"].append(1.0 if success else 0.0)
                    peer_up.labels(peer=peer_id).set(1.0 if success else 0.0)
                    if success:
                        peer_last_seen.labels(peer=peer_id).set(now)
                        _PEER_LAST_SUCCESS_TS[peer_id] = stats.get("last_success_ts", now)
                global _known_peers
                stale_peers = _known_peers - set(peer_ids)
                for peer_id in stale_peers:
                    peer_up.labels(peer=peer_id).set(0.0)
                    window = _peer_window(peer_id)
                    window["durations"].append(float(TIMEOUT))
                    window["success"].append(0.0)
                    peer_last_seen.labels(peer=peer_id).set(0.0)
                _known_peers = set(peer_ids)
                metrics["peers"].set(len(peer_ids))
                metrics["height"].set((checkpoint or {}).get("height", 0))
                now_success = time.time()
                metrics["last_result_ts"].labels(status="success").set(now_success)
                metrics["pull_result"].labels(status="success").inc()
                success_timestamp = now_success
            except Exception:
                peer_up = metrics.get("peer_up")
                if peer_up:
                    for peer_id in list(_known_peers):
                        peer_up.labels(peer=peer_id).set(0.0)
                        window = _peer_window(peer_id)
                        window["durations"].append(float(TIMEOUT))
                        window["success"].append(0.0)
                _update_empty_peers([], metrics)
                err_now = time.time()
                metrics["last_result_ts"].labels(status="error").set(err_now)
                metrics["pull_result"].labels(status="error").inc()
                peer_ids = []
            finally:
                quality_scores = _update_quality_metrics(metrics, params)
                current = time.time()
                last_success = success_timestamp
                if last_success is None:
                    last_success = metrics["last_result_ts"].labels(status="success")._value.get()
                _known_peers.clear()
                _known_peers.update(peer_ids)
                base_ready = bool(_known_peers) and last_success and (current - last_success) < 120
                _apply_quality_gate(bool(base_ready), quality_scores, metrics)
        with _lock:
            wait_interval = _CURRENT_INTERVAL
        _stop.wait(wait_interval)


def _update_empty_peers(peers: list[str], mets: dict) -> None:
    global _EMPTY_PEERS_STREAK, _LAST_EMPTY_PEERS_SIGNAL
    now = time.time()
    if not peers:
        _EMPTY_PEERS_STREAK += 1
        should_fire = (
            _EMPTY_PEERS_STREAK >= NO_PEERS_THRESHOLD
            and (now - _LAST_EMPTY_PEERS_SIGNAL) >= NO_PEERS_COOLDOWN
        )
        if should_fire:
            mets["remediation_events"].labels(reason="no_peers").inc()
            mets["pull_result"].labels(status="error").inc()
            _LAST_EMPTY_PEERS_SIGNAL = now
    else:
        _EMPTY_PEERS_STREAK = 0
