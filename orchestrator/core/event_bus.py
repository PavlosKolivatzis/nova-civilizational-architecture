import logging
from collections import defaultdict
from typing import Any, Callable, Dict, List


class EventBus:
    """Simple synchronous event bus with detailed metrics."""

    def __init__(self) -> None:
        self.handlers: Dict[str, List[Callable[[Dict[str, Any]], Any]]] = defaultdict(list)
        self.metrics: Dict[str, int] = {"events": 0}
        self.logger = logging.getLogger(__name__)

    def subscribe(self, event_type: str, handler: Callable[[Dict[str, Any]], Any]) -> None:
        self.handlers[event_type].append(handler)

    def publish(self, event_type: str, data: Dict[str, Any]) -> None:
        handlers = self.handlers.get(event_type, [])
        for handler in handlers:
            self.metrics["total_attempts"] = self.metrics.get("total_attempts", 0) + 1
            self.metrics["published"] = self.metrics.get("published", 0) + 1
            try:
                handler(data)
                self.metrics["events"] += 1
                self.metrics["successful_attempts"] = self.metrics.get("successful_attempts", 0) + 1
            except TimeoutError as e:  # pragma: no cover - not triggered in tests
                self.metrics["failed_attempts"] = self.metrics.get("failed_attempts", 0) + 1
                self.metrics["timeout_failures"] = self.metrics.get("timeout_failures", 0) + 1
                self.logger.error(f"Handler timeout: {e}")
                raise
            except Exception as e:
                self.metrics["failed_attempts"] = self.metrics.get("failed_attempts", 0) + 1
                self.metrics["exception_failures"] = self.metrics.get("exception_failures", 0) + 1
                self.logger.error(f"Handler failed: {e}")
                raise

    def get_success_rate(self) -> float:
        published = self.metrics.get("published", 0)
        successful = self.metrics.get("successful_attempts", 0)
        return successful / published if published > 0 else 1.0
