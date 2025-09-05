"""FastAPI application wiring for the orchestrator.

FastAPI is an optional dependency for this project.  The tests exercise the
core request handling without requiring the web framework.  Importing FastAPI
unconditionally would raise ``ModuleNotFoundError`` when the package is not
installed, causing pytest collection to fail.  To keep the module importable in
minimal environments, the import is guarded and the web routes are only created
when FastAPI is available.
"""

# Optional web framework (avoid import errors in environments without FastAPI)
try:  # pragma: no cover - absence of FastAPI is acceptable
    from fastapi import FastAPI
    from api.health_config import router as health_router
except ImportError:  # pragma: no cover - exercised when FastAPI isn't installed
    FastAPI = None  # type: ignore
    health_router = None  # type: ignore

from orchestrator.core.performance_monitor import PerformanceMonitor
from orchestrator.core.event_bus import EventBus, Event
from orchestrator.core import create_router, DEFAULT_FALLBACK_MAP
from logging_config import configure_logging

# Monitor, bus and router are created once and reused across requests
monitor = PerformanceMonitor()
bus = EventBus(monitor=monitor)
router = create_router(monitor)
configure_logging(level="INFO", json_format=True)

# Optional: configure fallbacks
# router.fallback_map = {"slot6": "slot6_fallback"}

SLOT_REGISTRY = {}
try:  # pragma: no cover - illustrative orchestrator wiring
    from orchestrator.run import Orchestrator  # type: ignore

    orch = Orchestrator(per_call_timeout=2.0, max_retries=1)
except Exception:  # pragma: no cover - orchestrator runner not available
    orch = None

if FastAPI is not None:
    app = FastAPI()
    if health_router is not None:
        app.include_router(health_router)

    @app.get("/health")
    async def health():
        slots = {sid: monitor.get_slot_health(sid) for sid in SLOT_REGISTRY.keys()}
        router_thresholds = {
            "latency_ms": getattr(router, "latency_threshold_ms", None),
            "error_rate": getattr(router, "error_threshold", None),
        }
        cb_metrics = router.cb.get_metrics() if getattr(router, "cb", None) else {}
        return {
            "status": "ok",
            "slots": slots,
            "router_thresholds": router_thresholds,
            "circuit_breaker": cb_metrics,
        }

    @app.on_event("startup")
    async def _startup():
        from slots.config import get_config_manager
        await get_config_manager()

    @app.on_event("shutdown")
    async def _shutdown():
        from slots.config import get_config_manager
        mgr = await get_config_manager()
        await mgr.shutdown()
else:  # pragma: no cover - FastAPI not installed
    app = None


async def handle_request(target_slot: str, payload: dict, request_id: str):
    """Route request based on slot health and invoke the orchestrator."""
    slot, timeout = router.get_route(target_slot, original_timeout=2.0)
    evt = Event(target_slot=slot, payload=payload)
    await bus.publish("invoke", evt)
    slot_fn = SLOT_REGISTRY.get(slot)
    if orch and slot_fn:
        return await orch.invoke_slot(slot_fn, slot, payload, request_id, timeout=timeout)
    return None
