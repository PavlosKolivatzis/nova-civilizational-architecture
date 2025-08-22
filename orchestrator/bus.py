from __future__ import annotations

import asyncio
import time
from collections import defaultdict
from dataclasses import dataclass
from typing import Any, Awaitable, Callable, Dict, List, DefaultDict

Handler = Callable[[Dict[str, Any]], Awaitable[Any]]

@dataclass
class BusMetrics:
    avg_handler_time: float = 0.0
    events: int = 0
    errors: int = 0

class EventBus:
    """Simple async publish/subscribe bus with per-handler timeout.

    Each handler is awaited with ``asyncio.wait_for`` using a default
    timeout of five seconds. Metrics are recorded as a rolling average of
    handler execution time and a total error counter. Errors include
    exceptions and timeout expirations.
    """

    def __init__(self, handler_timeout: float = 5.0) -> None:
        self._handlers: DefaultDict[str, List[Handler]] = defaultdict(list)
        self._timeout = handler_timeout
        self.metrics = BusMetrics()

    def subscribe(self, event: str, handler: Handler) -> None:
        """Register a handler for an event."""
        self._handlers[event].append(handler)

    async def publish(self, event: str, payload: Dict[str, Any]) -> List[Any]:
        """Publish an event and await all handlers.

        Returns a list with the result of each handler. Any handler that
        raises or times out is counted in the error metrics and omitted
        from the results list.
        """
        handlers = list(self._handlers.get(event, []))
        results: List[Any] = []
        for h in handlers:
            start = time.perf_counter()
            try:
                res = await asyncio.wait_for(h(payload), timeout=self._timeout)
                results.append(res)
                self._update_metrics(time.perf_counter() - start)
            except Exception:
                self.metrics.errors += 1
        return results

    def _update_metrics(self, duration: float) -> None:
        self.metrics.events += 1
        # exponential moving average without external deps
        self.metrics.avg_handler_time += (
            duration - self.metrics.avg_handler_time
        ) / self.metrics.events

    def snapshot(self) -> Dict[str, Any]:
        """Return a snapshot of the current metrics."""
        return {
            "avg_handler_time": self.metrics.avg_handler_time,
            "events": self.metrics.events,
            "errors": self.metrics.errors,
        }
