"""Contract emission infrastructure for Nova."""

from typing import Protocol, Any, Callable, List, Awaitable, Union
import logging
import asyncio

logger = logging.getLogger(__name__)


class ContractEmitter(Protocol):
    """Protocol for emitting contracts to slots."""
    def emit(self, contract: Any) -> None: ...


class NoOpEmitter:
    """Default no-operation emitter."""
    def emit(self, contract: Any) -> None:
        pass


_emitter: ContractEmitter = NoOpEmitter()
# Handlers can be sync or async callables accepting a single contract arg.
ContractHandler = Union[Callable[[Any], None], Callable[[Any], Awaitable[None]]]
_subscribers: List[ContractHandler] = []
_metrics = {
    "fanout_delivered": 0,
    "fanout_errors": 0,
}


def get_fanout_metrics() -> dict:
    """Snapshot of in-process fanout counters."""
    return dict(_metrics)


def set_contract_emitter(emitter: ContractEmitter) -> None:
    """Set the global contract emitter."""
    global _emitter
    _emitter = emitter


def get_contract_emitter() -> ContractEmitter:
    """Get the current contract emitter."""
    return _emitter


def subscribe(handler: ContractHandler) -> None:
    """Subscribe to in-process contract fanout (idempotent)."""
    if handler not in _subscribers:
        _subscribers.append(handler)


def unsubscribe(handler: ContractHandler) -> None:
    """Remove a previously subscribed handler (no-op if absent)."""
    try:
        _subscribers.remove(handler)
    except ValueError:
        pass


class _subscription:
    """Context manager for temporary subscriptions in tests."""
    def __init__(self, handler: ContractHandler):
        self._handler = handler

    def __enter__(self):
        subscribe(self._handler)
        return self._handler

    def __exit__(self, *exc):
        unsubscribe(self._handler)


def fanout(contract: Any) -> int:
    """
    Fan out contracts to local subscribers for immediate reactions.
    Returns number of handlers successfully scheduled/executed.
    """
    delivered = 0
    for handler in list(_subscribers):
        try:
            result = handler(contract)
            # If it's an async handler, schedule it without blocking.
            if asyncio.iscoroutine(result):
                try:
                    loop = asyncio.get_running_loop()
                    loop.create_task(result)  # fire-and-forget
                except RuntimeError:
                    # no loop running; fall back to synchronous execution
                    asyncio.run(result)
            _metrics["fanout_delivered"] += 1
            delivered += 1
        except Exception:
            _metrics["fanout_errors"] += 1
            logger.exception("Contract subscriber failed")
    return delivered


__all__ = [
    "ContractEmitter", "NoOpEmitter",
    "set_contract_emitter", "get_contract_emitter",
    "subscribe", "unsubscribe", "fanout", "_subscription",
    "get_fanout_metrics",
]
