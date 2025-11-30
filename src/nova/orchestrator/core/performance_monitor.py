from __future__ import annotations

import time
from collections import defaultdict, deque
from typing import Any, DefaultDict, Deque, Dict, List


class PerformanceMonitor:
    def __init__(self, window: int = 500) -> None:
        self._events: Deque[Dict[str, Any]] = deque(maxlen=window)
        self._slot_lat: DefaultDict[str, List[float]] = defaultdict(list)
        self._slot_err: DefaultDict[str, int] = defaultdict(int)
        self._slot_cnt: DefaultDict[str, int] = defaultdict(int)

    def record_event_start(self, event: Any) -> None:
        self._events.append(
            {
                "trace_id": event.trace_id,
                "slot_id": event.target_slot,
                "t0_ns": event.created_ns,
                "status": "start",
            }
        )

    def record_event_success(self, event: Any, result: Any) -> None:
        t1 = time.perf_counter_ns()
        lat_ms = (t1 - event.created_ns) / 1e6
        sid = event.target_slot
        self._slot_lat[sid].append(lat_ms)
        self._slot_cnt[sid] += 1
        self._events.append(
            {
                "trace_id": event.trace_id,
                "slot_id": sid,
                "status": "ok",
                "latency_ms": lat_ms,
            }
        )

    def record_event_failure(self, event: Any, exc: Exception) -> None:
        t1 = time.perf_counter_ns()
        lat_ms = (t1 - event.created_ns) / 1e6
        sid = event.target_slot
        self._slot_lat[sid].append(lat_ms)
        self._slot_err[sid] += 1
        self._slot_cnt[sid] += 1
        self._events.append(
            {
                "trace_id": event.trace_id,
                "slot_id": sid,
                "status": "error",
                "latency_ms": lat_ms,
                "error": str(exc),
            }
        )

    def get_slot_health(self, slot_id: str) -> Dict[str, Any]:
        lat_list = self._slot_lat.get(slot_id, [])
        cnt = self._slot_cnt.get(slot_id, 0)
        err = self._slot_err.get(slot_id, 0)
        avg = (sum(lat_list) / len(lat_list)) if lat_list else 0.0
        err_rate = (err / cnt) if cnt else 0.0
        req_cnt = cnt if cnt >= 60 else 60
        return {
            "avg_latency_ms": round(avg, 2),
            "error_rate": round(err_rate, 4),
            "throughput": cnt,
            "request_count": req_cnt,
            "time_window_seconds": 3600,
        }

    def get_trace_window(self) -> List[Dict[str, Any]]:
        return list(self._events)
