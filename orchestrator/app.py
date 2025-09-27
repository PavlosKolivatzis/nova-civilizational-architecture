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
    from fastapi import FastAPI, Response
    from api.health_config import router as health_router
    from contextlib import asynccontextmanager
except ImportError:  # pragma: no cover - exercised when FastAPI isn't installed
    FastAPI = None  # type: ignore
    health_router = None  # type: ignore

import asyncio
import time
import os
import logging

logger = logging.getLogger(__name__)

from orchestrator.core.performance_monitor import PerformanceMonitor
from orchestrator.core.event_bus import EventBus, Event
from orchestrator.core import create_router
from logging_config import configure_logging
from orchestrator.adapters import (
    Slot2DeltaThreshAdapter,
    Slot8MemoryEthicsAdapter,
    Slot9DistortionProtectionAdapter,
    Slot10DeploymentAdapter,
)
from orchestrator.health import health_payload, prometheus_metrics
import pkgutil
import slots

# Monitor, bus and router are created once and reused across requests
monitor = PerformanceMonitor()
bus = EventBus(monitor=monitor)
router = create_router(monitor)
configure_logging(level="INFO", json_format=True)

# Optional: configure fallbacks
# router.fallback_map = {"slot6": "slot6_fallback"}

SLOT_REGISTRY = {
    "slot02_deltathresh": Slot2DeltaThreshAdapter().process,
    "slot08_memory_ethics": Slot8MemoryEthicsAdapter().register,
    "slot09_distortion_protection": Slot9DistortionProtectionAdapter().detect,
    "slot10_civilizational_deployment": Slot10DeploymentAdapter().deploy,
}

# Registry of all slots for health/metrics aggregation (slots 1-10)
METRIC_SLOT_REGISTRY = {
    name: None
    for _, name, _ in pkgutil.iter_modules(slots.__path__)
    if name.startswith("slot")
}
try:  # pragma: no cover - illustrative orchestrator wiring
    from orchestrator.run import Orchestrator  # type: ignore

    orch = Orchestrator(per_call_timeout=2.0, max_retries=1)
except Exception:  # pragma: no cover - orchestrator runner not available
    orch = None

if FastAPI is not None:
    async def _sm_sweeper():
        interval = int(os.getenv("NOVA_SMEEP_INTERVAL", "15"))  # seconds
        logger.info("SemanticMirror sweeper starting (interval=%ss)", interval)
        while True:
            try:
                from orchestrator.semantic_mirror import get_semantic_mirror
                from orchestrator.prometheus_metrics import update_semantic_mirror_metrics
                sm = get_semantic_mirror()
                before = sm._metrics.get("entries_expired", 0)
                sm._cleanup_expired_entries(time.time())
                after = sm._metrics.get("entries_expired", 0)
                delta = after - before
                if delta:
                    logger.info("SemanticMirror sweeper tick: expired=%s", delta)
                update_semantic_mirror_metrics()  # keep /metrics in sync
            except Exception:
                logger.exception("SemanticMirror sweeper failed")
            await asyncio.sleep(interval)

    async def _canary_loop():
        """Periodically seed an expired, pulse-eligible context to verify the pipeline."""
        period = int(os.getenv("NOVA_UNLEARN_CANARY_PERIOD", "3600"))  # 1h
        if os.getenv("NOVA_UNLEARN_CANARY", "0") != "1":
            logger.info("Unlearn canary disabled")
            return

        key        = os.getenv("NOVA_UNLEARN_CANARY_KEY",        "slot06.cultural_profile")
        publisher  = os.getenv("NOVA_UNLEARN_CANARY_PUBLISHER",  "slot05")
        ttl        = float(os.getenv("NOVA_UNLEARN_CANARY_TTL",   "60"))   # >=60s to be eligible
        age_after  = float(os.getenv("NOVA_UNLEARN_CANARY_AGE",   "120"))  # age since expiry

        logger.info("Unlearn canary enabled (period=%ss, key=%s, ttl=%ss, age=%ss)",
                    period, key, ttl, age_after)

        while True:
            try:
                from orchestrator.semantic_mirror import get_semantic_mirror, ContextScope
                from types import SimpleNamespace
                sm = get_semantic_mirror()
                if not sm:
                    await asyncio.sleep(period)
                    continue

                now = time.time()
                created_ts = now - ttl - age_after  # so it's already expired by `age_after` seconds
                sm._contexts[key] = SimpleNamespace(
                    timestamp=created_ts,
                    ttl_seconds=ttl,
                    access_count=3,
                    scope=ContextScope.PUBLIC,
                    published_by=publisher,
                )
                # Track canary seeds for observability
                sm._metrics["canary_seeded"] = sm._metrics.get("canary_seeded", 0) + 1

                logger.info("Canary seeded: %s (ttl=%ss, age=%ss)", key, ttl, age_after)

                # Optionally trigger an immediate cleanup to produce a pulse now
                try:
                    sm._cleanup_expired_entries(time.time())
                except Exception:
                    logger.exception("Canary forced cleanup failed")
                    sm._metrics["canary_errors"] = sm._metrics.get("canary_errors", 0) + 1
            except Exception:
                logger.exception("Canary seeding failed")
                try:
                    from orchestrator.semantic_mirror import get_semantic_mirror
                    sm = get_semantic_mirror()
                    if sm:
                        sm._metrics["canary_errors"] = sm._metrics.get("canary_errors", 0) + 1
                except Exception:
                    pass
            await asyncio.sleep(period)

    async def _startup() -> None:
        from slots.config import get_config_manager
        await get_config_manager()

        # --- UNLEARN_PULSE emitter wiring ---
        import os, json
        from orchestrator.contracts.emitter import set_contract_emitter, NoOpEmitter

        class JsonlEmitter:
            """Append each UNLEARN_PULSE@1 as newline-delimited JSON with size-based rotation."""
            def __init__(self, path="logs/unlearn_pulses.ndjson", max_bytes=None, backups=None):
                self.path = path
                os.makedirs(os.path.dirname(path), exist_ok=True)
                self.max_bytes = int(os.getenv("NOVA_UNLEARN_LOG_MAX_BYTES", str(max_bytes or 10 * 1024 * 1024)))  # 10MB
                self.backups   = int(os.getenv("NOVA_UNLEARN_LOG_BACKUPS",  str(backups or 5)))

            def _rotate(self):
                if self.backups <= 0:
                    return
                # shift .N → .N+1
                for i in range(self.backups - 1, 0, -1):
                    src = f"{self.path}.{i}"
                    dst = f"{self.path}.{i+1}"
                    if os.path.exists(src):
                        os.replace(src, dst)
                # current → .1
                if os.path.exists(self.path):
                    os.replace(self.path, f"{self.path}.1")

            def emit(self, contract):
                try:
                    line = json.dumps(contract.model_dump()) + "\n"
                    # rotate if needed
                    if self.max_bytes and os.path.exists(self.path):
                        if os.path.getsize(self.path) + len(line.encode("utf-8")) > self.max_bytes:
                            self._rotate()
                    with open(self.path, "a", encoding="utf-8") as f:
                        f.write(line)
                except Exception:
                    logger.exception("JsonlEmitter failed")

        # Flip this to NoOpEmitter() to instantly disable delivery without redeploying logic
        path = os.getenv("NOVA_UNLEARN_PULSE_PATH", "logs/unlearn_pulses.ndjson")
        set_contract_emitter(JsonlEmitter(path))
        # set_contract_emitter(NoOpEmitter())  # <-- Rollback: uncomment this line

        # initialize zeros so series exist immediately
        from orchestrator.prometheus_metrics import update_semantic_mirror_metrics
        update_semantic_mirror_metrics()

        # register slot06 for unlearn pulse fanout
        from slots.slot06_cultural_synthesis.receiver import register_slot06_receiver
        register_slot06_receiver()

        # start periodic expiry in *this* process (the one Prometheus scrapes)
        asyncio.create_task(_sm_sweeper())

        # start canary loop (off by default)
        asyncio.create_task(_canary_loop())

    async def _shutdown() -> None:
        from slots.config import get_config_manager
        mgr = await get_config_manager()
        await mgr.shutdown()

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        await _startup()
        try:
            yield
        finally:
            await _shutdown()

    app = FastAPI(lifespan=lifespan)
    if health_router is not None:
        app.include_router(health_router)

    @app.get("/health")
    async def health():
        """Return aggregated health information for all slots."""
        payload = health_payload(
            METRIC_SLOT_REGISTRY, monitor, router, getattr(router, "cb", None)
        )
        payload["status"] = "ok"
        return payload

    @app.get("/metrics")
    async def metrics() -> Response:
        """Prometheus-compatible metrics for all slots."""
        import os
        flag = os.getenv("NOVA_ENABLE_PROMETHEUS", "false").strip().lower()
        if flag not in {"1", "true", "yes", "on"}:
            # Explicit 404 when disabled so scanners don't scrape it by default
            return Response(content=b"", status_code=404, media_type="text/plain")

        try:
            # New export path
            from orchestrator.prometheus_metrics import get_metrics_response
            data, content_type = get_metrics_response()
            return Response(content=data, media_type=content_type)
        except Exception:
            # Fallback to legacy implementation if the new exporter isn't available
            # Assumes these symbols already exist in this module's scope
            data = prometheus_metrics(METRIC_SLOT_REGISTRY, monitor)
            return Response(content=data, media_type="text/plain")

    @app.post("/ops/expire-now")
    async def force_expire():
        """Force semantic mirror cleanup for testing."""
        try:
            from types import SimpleNamespace
            from orchestrator.semantic_mirror import ContextScope, get_semantic_mirror
            from orchestrator.prometheus_metrics import update_semantic_mirror_metrics
            sm = get_semantic_mirror()
            if sm:
                # Optionally seed a pulse-eligible context (validation only)
                if os.getenv("NOVA_ALLOW_EXPIRE_TEST", "1") == "1":
                    key = "slot06.cultural_profile"  # documented, non-immune
                    if key not in sm._contexts:
                        now = time.time()
                        desired_age = float(os.getenv("NOVA_EXPIRE_TEST_AGE", "120"))  # seconds
                        sm._contexts[key] = SimpleNamespace(
                            timestamp=now - desired_age,    # created N seconds ago
                            ttl_seconds=60.0,               # >= 60 to qualify
                            access_count=3,                 # > 1
                            scope=ContextScope.PUBLIC,      # INTERNAL|PUBLIC
                            published_by="slot05"           # non-immune
                        )
                        logger.info("Created test context for pulse verification: %s (age=%ss)", key, desired_age)

                before_expired  = sm._metrics.get("entries_expired", 0)
                before_pulses   = sm._metrics.get("unlearn_pulses_sent", 0)
                before_contexts = len(sm._contexts)
                sm._cleanup_expired_entries(time.time() + 3600)  # force as "now"
                after_expired   = sm._metrics.get("entries_expired", 0)
                after_pulses    = sm._metrics.get("unlearn_pulses_sent", 0)
                after_contexts  = len(sm._contexts)
                update_semantic_mirror_metrics()

                return {
                    "status": "ok",
                    "expired_count": after_expired - before_expired,
                    "pulses_delta":  after_pulses  - before_pulses,
                    "contexts_before": before_contexts,
                    "contexts_after":  after_contexts,
                    "metrics": {
                        "entries_expired": after_expired,
                        "unlearn_pulses_sent": sm._metrics.get("unlearn_pulses_sent", 0),
                    },
                }
            else:
                return {"status": "no_mirror", "expired_count": 0}
        except Exception as e:
            logger.exception("expire-now failed")
            return {"status": "error", "error": str(e)}
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
