import asyncio
import uuid
import time
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional
from collections import defaultdict


@dataclass
class Event:
    target_slot: str
    payload: Dict[str, Any]
    trace_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    created_ns: int = field(default_factory=time.perf_counter_ns)


class _NullMonitor:
    def record_event_start(self, event):
        pass

    def record_event_success(self, event, result):
        pass

    def record_event_failure(self, event, exc):
        pass


class EventBus:
    def __init__(self, monitor: Optional[Any] = None) -> None:
        self._subs: Dict[str, List[Callable[[Event], Any]]] = defaultdict(list)
        self.monitor = monitor or _NullMonitor()
        self.metrics: Dict[str, int] = {"events": 0}

    def subscribe(self, topic: str, handler: Callable[[Event], Any]) -> None:
        self._subs[topic].append(handler)

    async def publish(self, topic: str, event: Event) -> List[Any]:
        self.monitor.record_event_start(event)
        handlers = self._subs.get(topic, [])
        results: List[Any] = []
        for h in handlers:
            self.metrics["total_attempts"] = self.metrics.get("total_attempts", 0) + 1
            self.metrics["published"] = self.metrics.get("published", 0) + 1
            try:
                res = h(event)
                if asyncio.iscoroutine(res):
                    res = await res
                results.append(res)
                self.metrics["events"] += 1
                self.metrics["successful_attempts"] = self.metrics.get("successful_attempts", 0) + 1
            except TimeoutError as e:  # pragma: no cover - rare
                self.metrics["failed_attempts"] = self.metrics.get("failed_attempts", 0) + 1
                self.metrics["timeout_failures"] = self.metrics.get("timeout_failures", 0) + 1
                self.monitor.record_event_failure(event, e)
                raise
            except Exception as e:
                self.metrics["failed_attempts"] = self.metrics.get("failed_attempts", 0) + 1
                self.metrics["exception_failures"] = self.metrics.get("exception_failures", 0) + 1
                self.monitor.record_event_failure(event, e)
                raise
        self.monitor.record_event_success(event, results if results else None)
        return results

    def get_success_rate(self) -> float:
        published = self.metrics.get("published", 0)
        successful = self.metrics.get("successful_attempts", 0)
        return successful / published if published > 0 else 1.0
