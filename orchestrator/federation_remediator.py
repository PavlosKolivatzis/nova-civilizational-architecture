"""Federation auto-remediation hooks."""

from __future__ import annotations

import logging
import os
import threading
import time
from typing import Any, Dict, Optional

from nova.federation.metrics import m

log = logging.getLogger("nova.federation.remediator")

_LAST_EVENT: Dict[str, Any] = {"reason": "none", "timestamp": 0.0, "interval": 0.0, "context": {}}
_LAST_EVENT_LOCK = threading.Lock()


def get_last_event() -> Dict[str, Any]:
    """Return a copy of the most recent remediation event metadata."""
    with _LAST_EVENT_LOCK:
        return dict(_LAST_EVENT)


class FederationRemediator:
    """Detect failure patterns in federation polling and trigger corrective actions."""

    def __init__(
        self,
        poller_module: Any,
        *,
        max_errors: int = 3,
        error_ratio_threshold: float = 0.5,
        ready_failures: int = 3,
        cooldown_seconds: float = 300.0,
        check_period: float = 30.0,
        restart_sleep: float = 5.0,
        max_backoff: Optional[float] = None,
    ) -> None:
        self.poller = poller_module
        self.max_errors = max_errors
        self.error_ratio_threshold = error_ratio_threshold
        self.max_ready_failures = ready_failures
        self.cooldown = cooldown_seconds
        self.check_period = check_period
        self.restart_sleep = restart_sleep
        self.metrics = m()
        self._stop = threading.Event()
        self._lock = threading.Lock()
        self._thread: Optional[threading.Thread] = None
        self._last_action_ts = 0.0
        self._ready_failures = 0
        self._last_config_error_ts = 0.0

        self._error_counter = self.metrics["pull_result"].labels(status="error")
        self._success_counter = self.metrics["pull_result"].labels(status="success")
        self._prev_errors = self._error_counter._value.get()
        self._prev_success = self._success_counter._value.get()

        self.base_interval = (
            self.poller.get_base_interval() if hasattr(self.poller, "get_base_interval") else self.poller.get_interval()
        )
        current_interval = self.poller.get_interval()
        self.max_backoff = max_backoff or max(self.base_interval * 8, current_interval)

    def start(self) -> None:
        with self._lock:
            if self._thread and self._thread.is_alive():
                return
            self._stop.clear()
            self._thread = threading.Thread(target=self._loop, name="federation-remediator", daemon=True)
            self._thread.start()

    def stop(self) -> None:
        with self._lock:
            self._stop.set()
            thread = self._thread
            self._thread = None
        if thread and thread.is_alive():
            thread.join(timeout=2.0)

    def _loop(self) -> None:
        while not self._stop.is_set():
            try:
                self._evaluate()
            except Exception:
                log.exception("Federation remediator evaluation failed")
            self._stop.wait(self.check_period)

    def _evaluate(self) -> None:
        ready_value = self.metrics["ready"]._value.get()
        if ready_value < 1.0:
            self._ready_failures += 1
        else:
            self._ready_failures = 0

        errors = self._error_counter._value.get()
        success = self._success_counter._value.get()
        delta_errors = errors - self._prev_errors
        delta_success = success - self._prev_success
        self._prev_errors = errors
        self._prev_success = success

        peer_count_metric = self.metrics.get("peers")
        peer_count = peer_count_metric._value.get() if peer_count_metric else 0
        if peer_count == 0 and self._can_log_config_error():
            self._record_config_error({"peer_count": peer_count})

        if self._ready_failures >= self.max_ready_failures and self._can_trigger():
            self._trigger("readiness_zero", {"ready_failures": self._ready_failures})
            return

        if delta_errors >= self.max_errors:
            total = delta_errors + delta_success
            ratio = delta_errors / total if total else 1.0
            if ratio >= self.error_ratio_threshold and self._can_trigger():
                self._trigger(
                    "error_spike",
                    {
                        "delta_errors": delta_errors,
                        "delta_success": delta_success,
                        "ratio": ratio,
                    },
                )
                return

        # Recover backoff when things look good again
        if ready_value >= 1.0 and delta_errors == 0:
            current_interval = self.poller.get_interval()
            if current_interval > self.base_interval:
                new_interval = self.poller.set_interval(self.base_interval)
                self._record_event("backoff_reset", new_interval, update_last=False, context={"previous": current_interval})

    def _can_trigger(self) -> bool:
        return (time.time() - self._last_action_ts) >= self.cooldown

    def _can_log_config_error(self) -> bool:
        return (time.time() - self._last_config_error_ts) >= self.cooldown

    def _trigger(self, reason: str, context: Dict[str, Any]) -> None:
        with self._lock:
            if not self._can_trigger():
                return
            # P1 Configurable Thresholds (Phase 17 Audit Fix)
            backoff_multiplier = float(os.getenv("NOVA_FEDERATION_BACKOFF_MULTIPLIER", "2.0"))
            current_interval = self.poller.get_interval()
            proposed = max(current_interval if current_interval else self.base_interval, self.base_interval)
            proposed = min(proposed * backoff_multiplier, self.max_backoff)
            try:
                self.poller.stop()
            except Exception:
                log.exception("Failed stopping federation poller during remediation")
            new_interval = self.poller.set_interval(proposed)
            time.sleep(self.restart_sleep)
            try:
                self.poller.start()
            except Exception:
                log.exception("Failed restarting federation poller during remediation")

            timestamp = time.time()
            self._record_event(reason, new_interval, timestamp=timestamp, context=context)
            self._ready_failures = 0
            self._last_action_ts = timestamp
            log.warning(
                "Federation auto-remediation triggered: %s (interval %.2fs, context=%s)",
                reason,
                new_interval,
                context,
            )

    def _record_config_error(self, context: Dict[str, Any]) -> None:
        with self._lock:
            timestamp = time.time()
            self._record_event(
                "config_error",
                self.poller.get_interval(),
                timestamp=timestamp,
                context=context,
                update_last=False,
            )
            self._last_config_error_ts = timestamp
        log.warning("Federation configuration issue detected: no peers configured")

    def _record_event(
        self,
        reason: str,
        interval: float,
        *,
        timestamp: Optional[float] = None,
        context: Optional[Dict[str, Any]] = None,
        update_last: bool = True,
    ) -> None:
        if timestamp is None:
            timestamp = time.time()
        self.metrics["remediation_events"].labels(reason=reason).inc()
        if update_last:
            self.metrics["remediation_last_action"].set(timestamp)
            self._last_action_ts = timestamp
        self.metrics["remediation_backoff"].set(interval)
        self.metrics["remediation_last_event"].info(
            {
                "reason": reason,
                "interval": f"{interval:.2f}",
                "timestamp": str(int(timestamp)),
            }
        )
        with _LAST_EVENT_LOCK:
            _LAST_EVENT.update(
                {
                    "reason": reason,
                    "timestamp": timestamp,
                    "interval": interval,
                    "context": context or {},
                }
            )

