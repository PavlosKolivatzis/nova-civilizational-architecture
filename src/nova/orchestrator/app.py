# ruff: noqa: E402
"""FastAPI application wiring for the orchestrator.

FastAPI is an optional dependency for this project.  The tests exercise the
core request handling without requiring the web framework.  Importing FastAPI
unconditionally would raise `ModuleNotFoundError` when the package is not
installed, causing pytest collection to fail.  To keep the module importable in
minimal environments, the import is guarded and the web routes are only created
when FastAPI is available.
"""

import asyncio
import logging
import os
import pkgutil
import sys
import time
from contextlib import asynccontextmanager
from typing import Optional

import nova.slots as nova_slots
from src_bootstrap import ensure_src_on_path

ensure_src_on_path()

from nova.logging_config import configure_logging
from nova.orchestrator.adapters import (
    Slot10DeploymentAdapter,
    Slot2DeltaThreshAdapter,
    Slot8MemoryEthicsAdapter,
    Slot9DistortionProtectionAdapter,
)
from nova.orchestrator.core import create_router
from nova.orchestrator.core.event_bus import Event, EventBus
from nova.orchestrator.core.performance_monitor import PerformanceMonitor
from nova.orchestrator.health import health_payload, prometheus_metrics
from nova.orchestrator.router.epistemic_router import EpistemicRouter
from nova.orchestrator.router.temporal_constraints import TemporalConstraintEngine
from nova.orchestrator.governance import GovernanceEngine, GovernanceLedger
from nova.orchestrator.temporal import TemporalLedger
from nova.orchestrator.temporal.adapters import read_temporal_snapshot, read_temporal_ledger_head
from nova.orchestrator.predictive import PredictiveLedger, PredictiveTrajectoryEngine

logger = logging.getLogger(__name__)

# Load environment variables from .env file (Phase 2: production hardening)
try:
    from dotenv import load_dotenv
except ImportError:  # python-dotenv not installed; env must be set externally
    load_dotenv = None  # type: ignore[assignment]
else:
    load_dotenv()

# Optional web framework (avoid import errors in environments without FastAPI)
try:  # pragma: no cover - absence of FastAPI is acceptable
    from fastapi import FastAPI, Response, status, HTTPException, Request
    from fastapi.responses import JSONResponse
except ImportError:  # pragma: no cover - exercised when FastAPI isn't installed
    FastAPI = None  # type: ignore[assignment]
    Response = None  # type: ignore[assignment]
    status = None  # type: ignore[assignment]
    HTTPException = None  # type: ignore[assignment]
    Request = None  # type: ignore[assignment]
    JSONResponse = None  # type: ignore[assignment]
    health_router = None  # type: ignore[assignment]
    reflection_router = None  # type: ignore[assignment]
    Limiter = None  # type: ignore[assignment]
    _rate_limit_exceeded_handler = None  # type: ignore[assignment]
    get_remote_address = None  # type: ignore[assignment]
    RateLimitExceeded = None  # type: ignore[assignment]
else:
    try:
        from api.health_config import router as health_router
    except ImportError:  # pragma: no cover - optional router
        health_router = None  # type: ignore[assignment]
    try:
        from nova.orchestrator.reflection import router as reflection_router
    except ImportError:  # pragma: no cover - optional router
        reflection_router = None  # type: ignore[assignment]

    try:
        # Phase 17: Rate limiting for DoS protection (CR-3)
        from slowapi import Limiter, _rate_limit_exceeded_handler
        from slowapi.util import get_remote_address
        from slowapi.errors import RateLimitExceeded
    except ImportError:  # pragma: no cover - exercised when slowapi isn't installed
        Limiter = None  # type: ignore[assignment]
        _rate_limit_exceeded_handler = None  # type: ignore[assignment]
        get_remote_address = None  # type: ignore[assignment]
        RateLimitExceeded = None  # type: ignore[assignment]
# Monitor, bus and router are created once and reused across requests
monitor = PerformanceMonitor()
bus = EventBus(monitor=monitor)
router = create_router(monitor)
temporal_ledger = TemporalLedger()
temporal_constraint_engine = TemporalConstraintEngine(ledger=temporal_ledger)
predictive_ledger = PredictiveLedger()
predictive_engine = PredictiveTrajectoryEngine(ledger=predictive_ledger)
deterministic_router = EpistemicRouter(temporal_engine=temporal_constraint_engine)
governance_ledger = GovernanceLedger()
governance_engine = GovernanceEngine(
    governance_ledger,
    temporal_ledger=temporal_ledger,
    predictive_engine=predictive_engine,
)
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
    for _, name, _ in pkgutil.iter_modules(nova_slots.__path__)
    if name.startswith("slot")
}
try:  # pragma: no cover - illustrative orchestrator wiring
    from nova.orchestrator.run import Orchestrator  # type: ignore

    orch = Orchestrator(per_call_timeout=2.0, max_retries=1)
except Exception:  # pragma: no cover - orchestrator runner not available
    orch = None

_peer_store = None
_peer_sync = None


def get_peer_store():
    """
    Expose the current PeerStore instance (if initialized).

    Deprecated: Use orchestrator.peer_store_singleton.get_peer_store() instead.
    This remains for backward compatibility only.
    """
    from nova.orchestrator.peer_store_singleton import get_peer_store as get_singleton
    return get_singleton()

SECURITY_HEADERS = {
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "X-XSS-Protection": "1; mode=block",
    "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
}


if FastAPI is not None:
    _federation_metrics_thread = None
    _federation_remediator = None
    _wisdom_poller_thread = None

    async def _sm_sweeper():
        interval = int(os.getenv("NOVA_SMEEP_INTERVAL", "15"))  # seconds
        logger.info("SemanticMirror sweeper starting (interval=%ss)", interval)

        # Lazy import to avoid hard dependency when flag is off
        try:
            from nova.orchestrator.unlearn_weighting import update_anomaly_inputs
        except Exception:
            update_anomaly_inputs = None

        sweep_count = 0
        while True:
            try:
                from nova.orchestrator.semantic_mirror import get_semantic_mirror
                from nova.orchestrator.prometheus_metrics import update_semantic_mirror_metrics
                sm = get_semantic_mirror()

                # --- Feed anomaly inputs (flag-gated) ---
                if update_anomaly_inputs and os.getenv("NOVA_UNLEARN_ANOMALY", "0") == "1":
                    tri = {}
                    try:
                        # Best-effort TRI drift/jitter collection via ACL-respecting get_context
                        tri_drift = sm.get_context("slot04.tri_drift_z", "anomaly_detector")
                        phase_jitter = sm.get_context("slot04.phase_jitter", "anomaly_detector")
                        if tri_drift is not None:
                            tri["drift_z"] = float(tri_drift)
                        if phase_jitter is not None:
                            tri["phase_jitter"] = float(phase_jitter)
                    except Exception:
                        tri = {}

                    # System pressure (best-effort; fallback to 0.0)
                    system = {}
                    try:
                        pressure = sm.get_context("slot07.pressure_level", "anomaly_detector")
                        if pressure is not None:
                            system["system_pressure_level"] = float(pressure)
                        else:
                            system["system_pressure_level"] = 0.0
                    except Exception:
                        system = {"system_pressure_level": 0.0}

                    update_anomaly_inputs(tri, system)

                    # Optional low-frequency debug logging for ops correlation
                    sweep_count += 1
                    if sweep_count % 10 == 0:  # every 10th sweep
                        try:
                            from nova.orchestrator.unlearn_weighting import get_anomaly_observability
                            ao = get_anomaly_observability()
                            logger.debug("Anomaly state: score=%.3f multiplier=%.2f engaged=%s",
                                       ao.get("score", 0.0), ao.get("multiplier", 1.0),
                                       bool(ao.get("engaged", 0.0)))
                        except Exception:
                            pass

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
                from nova.orchestrator.semantic_mirror import get_semantic_mirror, ContextScope
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
                    from nova.orchestrator.semantic_mirror import get_semantic_mirror
                    sm = get_semantic_mirror()
                    if sm:
                        sm._metrics["canary_errors"] = sm._metrics.get("canary_errors", 0) + 1
                except Exception:
                    pass
            await asyncio.sleep(period)

    async def _startup() -> None:
        from nova.slots.config import get_config_manager
        await get_config_manager()

        logging.getLogger("wisdom_poller").setLevel(logging.DEBUG)

        # --- UNLEARN_PULSE emitter wiring ---
        import os
        import json
        from nova.orchestrator.contracts.emitter import set_contract_emitter

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
        from nova.orchestrator.prometheus_metrics import update_semantic_mirror_metrics
        update_semantic_mirror_metrics()

        # initialize flow fabric with known contract links
        try:
            from nova.orchestrator.flow_fabric_init import initialize_flow_fabric
            initialize_flow_fabric()
        except Exception as e:
            logger.warning(f"Flow fabric initialization failed: {e}")

        # register slot06 for unlearn pulse fanout
        from nova.slots.slot06_cultural_synthesis.receiver import register_slot06_receiver
        register_slot06_receiver()

        # Wire Slot 7 production controls reflex bus into adaptive links
        try:
            from nova.orchestrator.reflex_signals import setup_slot7_reflex_integration

            setup_slot7_reflex_integration()
        except Exception as exc:
            logger.warning("Slot7 reflex integration skipped: %s", exc)

        # Phase 2: Initialize creativity governor and log config
        try:
            from nova.orchestrator.semantic_creativity import get_creativity_governor
            governor = get_creativity_governor()
            logger.info("CreativityGovernor initialized at startup")
            logger.info(f"Config: early_stop={governor.config.early_stop_enabled}, "
                       f"two_phase={governor.config.two_phase_depth_enabled}, "
                       f"bnb={governor.config.bnb_enabled}")
        except Exception as e:
            logger.warning(f"CreativityGovernor initialization failed: {e}")

        prom_enabled = os.getenv("NOVA_ENABLE_PROMETHEUS", "0").strip() == "1"
        federation_enabled = os.getenv("FEDERATION_ENABLED", "0").strip() == "1"
        if prom_enabled and federation_enabled:
            try:
                from nova.orchestrator import federation_poller

                global _federation_metrics_thread, _federation_remediator
                _federation_metrics_thread = federation_poller.start()
                auto_remediate_env = os.getenv("NOVA_FEDERATION_AUTOREMEDIATE")
                if auto_remediate_env is None:
                    auto_remediate_env = os.getenv("FEDERATION_AUTOREMEDIATE", "1")
                auto_remediate = auto_remediate_env.strip() == "1"
                if auto_remediate:
                    try:
                        from nova.orchestrator.federation_remediator import FederationRemediator

                        _federation_remediator = FederationRemediator(federation_poller)
                        _federation_remediator.start()
                    except Exception:
                        _federation_remediator = None
                        logger.exception("Failed to start federation remediator")
                else:
                    _federation_remediator = None
                    logger.info(
                        "Federation auto-remediation disabled via NOVA_FEDERATION_AUTOREMEDIATE/FEDERATION_AUTOREMEDIATE"
                    )
                logger.info(
                    "Federation metrics poller started (interval=%ss timeout=%ss)",
                    federation_poller.INTERVAL,
                    federation_poller.TIMEOUT,
                )
            except Exception:
                logger.exception("Failed to start federation metrics poller")

        # Phase 16-2: Peer synchronization (before wisdom poller to ensure _peer_store available)
        peer_sync_enabled = os.getenv("NOVA_FED_SYNC_ENABLED", "0") == "1"
        if peer_sync_enabled:
            try:
                from nova.orchestrator.federation_synchronizer import PeerStore, PeerSync

                from nova.orchestrator.peer_store_singleton import init_peer_store

                global _peer_store, _peer_sync
                _peer_store = PeerStore()
                init_peer_store(_peer_store)  # Register singleton
                _peer_sync = PeerSync(_peer_store)
                _peer_sync.start()
                logger.info(
                    "Peer sync started (peers=%d, interval=%ss)",
                    len(_peer_sync._peers),
                    _peer_sync._interval,
                )
            except Exception:
                logger.exception("Failed to start peer sync")

        # Adaptive wisdom governor (Phase 15-8)
        wisdom_enabled = os.getenv("NOVA_WISDOM_GOVERNOR_ENABLED", "0").strip() == "1"
        if prom_enabled and wisdom_enabled:
            try:
                from nova.orchestrator import adaptive_wisdom_poller

                global _wisdom_poller_thread
                _wisdom_poller_thread = adaptive_wisdom_poller.start()
                logger.info(
                    "Adaptive wisdom poller started (interval=%ss)",
                    adaptive_wisdom_poller.get_interval(),
                )
            except Exception:
                logger.exception("Failed to start adaptive wisdom poller")

        # start periodic expiry in *this* process (the one Prometheus scrapes)
        asyncio.create_task(_sm_sweeper())

        # start canary loop (off by default)
        asyncio.create_task(_canary_loop())

    async def _shutdown() -> None:
        global _federation_metrics_thread, _federation_remediator, _wisdom_poller_thread, _peer_sync
        if _federation_remediator:
            try:
                _federation_remediator.stop()
            except Exception:
                logger.exception("Failed to stop federation remediator")
            finally:
                _federation_remediator = None
        if _federation_metrics_thread:
            try:
                from nova.orchestrator import federation_poller

                federation_poller.stop()
                _federation_metrics_thread.join(timeout=1.0)
            except Exception:
                logger.exception("Failed to stop federation metrics poller")
            finally:
                _federation_metrics_thread = None
        if _wisdom_poller_thread:
            try:
                from nova.orchestrator import adaptive_wisdom_poller

                adaptive_wisdom_poller.stop()
                _wisdom_poller_thread.join(timeout=1.0)
            except Exception:
                logger.exception("Failed to stop adaptive wisdom poller")
            finally:
                _wisdom_poller_thread = None

        # Phase 16-2: Peer synchronization
        if _peer_sync:
            try:
                _peer_sync.stop()
            except Exception:
                logger.exception("Failed to stop peer sync")
            finally:
                _peer_sync = None

        from nova.slots.config import get_config_manager
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

    # Phase 17: Rate limiting for DoS protection (CR-3)
    if Limiter is not None:
        limiter = Limiter(
            key_func=get_remote_address,
            default_limits=["1000/hour", "100/minute"],  # Global baseline
            enabled=os.getenv("NOVA_RATE_LIMITING_ENABLED", "1") == "1"  # Default ON
        )
        app.state.limiter = limiter
        app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
    else:
        limiter = None

    if health_router is not None:
        app.include_router(health_router)
    if reflection_router is not None:
        app.include_router(reflection_router)
    try:
        from nova.ledger.api_checkpoints import checkpoint_router
        app.include_router(checkpoint_router)
        logger.info("Ledger checkpoint router enabled (in-memory mode - see api_checkpoints.py for limitations)")
    except Exception:
        logger.warning("Failed to add ledger checkpoint router")
    try:
        from nova.federation.federation_server import build_router as build_federation_router
    except Exception:  # pragma: no cover - federation optional
        build_federation_router = None  # type: ignore
    if build_federation_router is not None:
        federation_router = build_federation_router()
        if federation_router is not None:
            app.include_router(federation_router)
            # Remove legacy federation health route to allow observability override
            for _route in list(app.router.routes):
                if getattr(_route, "path", None) == "/federation/health" and "GET" in getattr(_route, "methods", set()):
                    app.router.routes.remove(_route)
                    break

    # Phase 16-2: Peer sync route
    try:
        from nova.orchestrator.routes.peer_sync import create_peer_sync_router
        peer_sync_router = create_peer_sync_router()
        if peer_sync_router is not None:
            app.include_router(peer_sync_router)
    except Exception:
        logger.warning("Failed to add peer sync router")

    @app.middleware("http")
    async def add_security_headers(request: Request, call_next):
        """Attach security headers to every HTTP response."""
        response = await call_next(request)
        for header, value in SECURITY_HEADERS.items():
            response.headers.setdefault(header, value)
        return response

    @app.get("/health")
    async def health():
        """Return aggregated health information for all slots."""
        payload = health_payload(
            METRIC_SLOT_REGISTRY, monitor, router, getattr(router, "cb", None)
        )
        payload["status"] = "ok"
        return payload

    @app.get("/ready")
    async def ready_probe():
        """Readiness probe that mirrors the federation readiness gauge."""
        try:
            from nova.orchestrator.federation_health import get_peer_health
        except Exception as exc:  # pragma: no cover - readiness optional
            logger.exception("failed to import federation health probe")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"federation readiness unavailable: {exc}",
            ) from exc

        try:
            health = get_peer_health()
        except Exception:
            logger.exception("readiness health probe failed")
            return JSONResponse(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                content={"ready": False},
            )

        is_ready = bool(health.get("ready"))

        try:
            from nova.federation.metrics import m
            ready_gauge = m().get("ready")
            if ready_gauge is not None:
                is_ready = bool(ready_gauge._value.get() == 1.0)
        except Exception:
            logger.exception("failed to read readiness gauge")

        status_code = status.HTTP_200_OK if is_ready else status.HTTP_503_SERVICE_UNAVAILABLE
        return JSONResponse(content={"ready": is_ready}, status_code=status_code)

    @app.get("/federation/health")
    async def federation_health():
        """Return current federation health telemetry."""
        try:
            from nova.orchestrator.federation_health import get_peer_health
        except Exception as exc:  # pragma: no cover - health optional
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"federation health unavailable: {exc}",
            ) from exc

        try:
            return get_peer_health()
        except Exception as exc:  # pragma: no cover - health optional
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"federation health collection failed: {exc}",
            ) from exc

    def _update_phase10_metrics():
        """Update Phase 10 Prometheus metrics from module state."""
        try:
            from nova.orchestrator.phase10_manager import get_phase10_manager
            from nova.orchestrator.prometheus_metrics import (
                phase10_eai_gauge,
                phase10_eai_gauge_public,
                phase10_fcq_gauge,
                phase10_fcq_gauge_public,
                phase10_cgc_gauge,
                phase10_cgc_gauge_public,
                phase10_pis_gauge,
                phase10_pis_gauge_public,
                phase10_ag_throttle_counter,
                phase10_ag_throttle_counter_public,
                phase10_ag_escalation_counter,
                phase10_ag_escalation_counter_public,
            )

            mgr = get_phase10_manager()

            # Update gauges
            ag_metrics = mgr.ag.get_metrics()
            pcr_metrics = mgr.pcr.get_metrics()
            cig_metrics = mgr.cig.get_metrics()

            eai_value = ag_metrics["eai"]
            cgc_value = cig_metrics["cgc"]
            pis_value = pcr_metrics["pis"]

            phase10_eai_gauge.labels(deployment="local").set(eai_value)
            phase10_eai_gauge_public.labels(deployment="local").set(eai_value)
            phase10_fcq_gauge.labels(decision="autonomy_governor").set(ag_metrics.get("fcq", 0.0))
            phase10_fcq_gauge_public.labels(decision="autonomy_governor").set(ag_metrics.get("fcq", 0.0))
            phase10_cgc_gauge.labels(mesh="global").set(cgc_value)
            phase10_cgc_gauge_public.labels(mesh="global").set(cgc_value)
            phase10_pis_gauge.labels(ledger="pcr").set(pis_value)
            phase10_pis_gauge_public.labels(ledger="pcr").set(pis_value)

            # Update counters (set to current totals; Prometheus handles deltas)
            throttle_total = ag_metrics["throttle_events_total"]
            escalation_total = ag_metrics["escalation_events_total"]
            phase10_ag_throttle_counter._value._value = throttle_total
            phase10_ag_throttle_counter_public._value._value = throttle_total
            phase10_ag_escalation_counter._value._value = escalation_total
            phase10_ag_escalation_counter_public._value._value = escalation_total

        except Exception as e:
            logger.warning(f"Phase 10 metrics update failed: {e}")

    @app.get("/federation/health")
    async def federation_health():
        """Return current federation health telemetry."""
        try:
            from nova.orchestrator.federation_health import get_peer_health
        except Exception as exc:  # pragma: no cover - health optional
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"federation health unavailable: {exc}",
            ) from exc

        return get_peer_health()
    @app.get("/metrics")
    async def metrics() -> Response:
        """Prometheus-compatible metrics for all slots."""
        import os
        flag = os.getenv("NOVA_ENABLE_PROMETHEUS", "0").strip()
        if flag != "1":
            # Explicit 404 when disabled so scanners don't scrape it by default
            return Response(content=b"", status_code=404, media_type="text/plain")

        try:
            # New export path
            from nova.orchestrator.prometheus_metrics import get_metrics_response
            # Phase 10: Update metrics before export
            _update_phase10_metrics()
            data, content_type = get_metrics_response()
            return Response(content=data, media_type=content_type)
        except Exception:
            # Fallback to legacy implementation if the new exporter isn't available
            # Assumes these symbols already exist in this module's scope
            data = prometheus_metrics(METRIC_SLOT_REGISTRY, monitor)
            return Response(content=data, media_type="text/plain")

    @app.get("/metrics/internal")
    async def metrics_internal() -> Response:
        """Internal Prometheus metrics (slot-level)."""
        import os
        flag = os.getenv("NOVA_ENABLE_PROMETHEUS", "0").strip()
        if flag != "1":
            return Response(content=b"", status_code=404, media_type="text/plain")

        from nova.orchestrator.prometheus_metrics import get_internal_metrics_response
        _update_phase10_metrics()
        data, content_type = get_internal_metrics_response()
        return Response(content=data, media_type=content_type)

    @app.post("/router/decide")
    async def router_decide(payload: Optional[dict] = None):
        """Deterministic routing decision endpoint."""
        payload = payload or {}
        precheck = governance_engine.evaluate(payload, record=False)
        if not precheck.allowed:
            return {
                "route": "hold",
                "governance": precheck.to_dict(),
                "constraints": {
                    "allowed": False,
                    "reasons": ["governance_precheck"],
                    "snapshot": {},
                },
            }

        decision = deterministic_router.decide(payload)
        decision_dict = decision.to_dict()
        enriched_state = dict(payload)
        enriched_state["routing_decision"] = decision_dict
        final_governance = governance_engine.evaluate(
            enriched_state,
            routing_decision=decision_dict,
            record=True,
        )
        response = dict(decision_dict)
        response["governance"] = final_governance.to_dict()
        return response

    @app.get("/router/debug")
    async def router_debug():
        """Return the latest routing decision (or generate one with safe defaults)."""
        last_decision = deterministic_router.last_decision
        if last_decision is None:
            last_decision = deterministic_router.decide({})
        body = last_decision.to_dict()
        body.setdefault("metadata", {})["mode"] = "deterministic"
        governance = governance_engine.last_result
        if governance:
            body["governance"] = governance.to_dict()
        return body

    @app.post("/governance/evaluate")
    async def governance_evaluate(payload: Optional[dict] = None):
        """Evaluate governance state directly."""
        result = governance_engine.evaluate(payload or {})
        return result.to_dict()

    @app.get("/governance/debug")
    async def governance_debug():
        """Return last governance evaluation."""
        last = governance_engine.last_result
        if last is None:
            last = governance_engine.evaluate({}, record=False)
        return last.to_dict()

    # Phase 10: FEP (Federated Ethical Protocol) endpoints
    @app.post("/phase10/fep/proposal")
    @limiter.limit("10/minute") if limiter else lambda f: f  # CR-3: DoS protection
    async def fep_submit_proposal(request: Request, payload: dict):
        """Submit ethical decision proposal for federated voting."""
        from nova.orchestrator.phase10_manager import get_phase10_manager
        mgr = get_phase10_manager()
        result = mgr.fep.submit_proposal(
            decision_id=payload["decision_id"],
            topic=payload["topic"],
            **payload.get("options", {})
        )
        return result

    @app.post("/phase10/fep/vote")
    @limiter.limit("100/hour") if limiter else lambda f: f  # CR-3: DoS protection
    async def fep_vote(request: Request, payload: dict):
        """Cast vote on FEP proposal."""
        from nova.orchestrator.phase10_manager import get_phase10_manager
        mgr = get_phase10_manager()
        result = mgr.fep.vote(
            decision_id=payload["decision_id"],
            node_id=payload["node_id"],
            alignment=payload["alignment"],
            weight=payload.get("weight", 1.0),
            dissent_reason=payload.get("dissent_reason"),
        )
        # Record in PCR after vote
        return result

    @app.post("/phase10/fep/finalize")
    @limiter.limit("1/minute") if limiter else lambda f: f  # CR-3: DoS protection
    async def fep_finalize(request: Request, payload: dict):
        """Finalize FEP decision and record in PCR."""
        from nova.orchestrator.phase10_manager import get_phase10_manager
        mgr = get_phase10_manager()

        # AG boundary check
        boundary = mgr.ag.check_decision_boundary()
        if boundary["action"] != "proceed":
            return {
                "error": "ag_blocked",
                "action": boundary["action"],
                "reason": boundary["reason"],
                "eai": boundary["eai"],
            }

        # Finalize decision
        decision = mgr.fep.finalize(payload["decision_id"])

        # Record in PCR
        mgr.pcr.append(
            decision_id=decision.id,
            decision_hash=decision.provenance["hash"],
        )

        # Update AG
        mgr.ag.record_decision(safe=decision.is_approved())

        return {
            "status": "finalized",
            "decision_id": decision.id,
            "fcq": decision.fcq,
            "approved": decision.is_approved(),
        }

    @app.get("/phase10/metrics")
    async def phase10_metrics():
        """Export Phase 10 operational metrics."""
        from nova.orchestrator.phase10_manager import get_phase10_manager
        mgr = get_phase10_manager()
        return {
            "fep": mgr.fep.get_metrics(),
            "pcr": mgr.pcr.get_metrics(),
            "ag": mgr.ag.get_metrics(),
            "cig": mgr.cig.get_metrics(),
            "fle": mgr.fle.get_metrics(),
        }

    @app.post("/ops/expire-now")
    @limiter.limit("1/10minutes") if limiter else lambda f: f  # CR-3: DoS protection
    async def force_expire(request: Request):
        """Force semantic mirror cleanup for testing."""
        try:
            from types import SimpleNamespace
            from nova.orchestrator.semantic_mirror import ContextScope, get_semantic_mirror
            from nova.orchestrator.prometheus_metrics import update_semantic_mirror_metrics
            sm = get_semantic_mirror()
            if sm:
                # Optionally seed a pulse-eligible context (validation only)
                # P1-MR1: Test functionality disabled by default (security)
                if os.getenv("NOVA_ALLOW_EXPIRE_TEST", "0") == "1":
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


@app.get("/temporal/snapshot")
async def temporal_snapshot():
    mirror_snapshot = read_temporal_snapshot("temporal_api")
    if mirror_snapshot:
        return {"snapshot": mirror_snapshot}
    return {"snapshot": temporal_ledger.head()}


@app.get("/temporal/ledger")
async def temporal_ledger_endpoint():
    entries = temporal_ledger.snapshot()
    if entries:
        return {"entries": entries}
    head = read_temporal_ledger_head("temporal_api")
    return {"entries": [head] if head else []}


@app.get("/temporal/debug")
async def temporal_debug():
    return {
        "entries": len(temporal_ledger.snapshot()),
        "head": temporal_ledger.head(),
    }


@app.get("/predictive/ledger")
async def predictive_ledger_endpoint():
    return {"entries": predictive_ledger.snapshot()}


@app.get("/predictive/debug")
async def predictive_debug():
    return {
        "entries": len(predictive_ledger.snapshot()),
        "head": predictive_ledger.head(),
    }


@app.get("/metrics/temporal")
async def metrics_temporal() -> Response:
    flag = os.getenv("NOVA_ENABLE_PROMETHEUS", "0").strip()
    if flag != "1":
        return Response(content=b"", status_code=404, media_type="text/plain")
    from nova.orchestrator.prometheus_metrics import get_temporal_metrics_response

    data, content_type = get_temporal_metrics_response()
    return Response(content=data, media_type=content_type)


@app.get("/metrics/predictive")
async def metrics_predictive() -> Response:
    flag = os.getenv("NOVA_ENABLE_PROMETHEUS", "0").strip()
    if flag != "1":
        return Response(content=b"", status_code=404, media_type="text/plain")
    from nova.orchestrator.prometheus_metrics import get_predictive_metrics_response

    data, content_type = get_predictive_metrics_response()
    return Response(content=data, media_type=content_type)
