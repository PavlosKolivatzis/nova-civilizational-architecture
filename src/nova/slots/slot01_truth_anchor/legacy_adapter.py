"""
NOVA Slot 1: Legacy Orchestrator Adapter (Pre-Root-Mode)
Preserved for fallback when NOVA_SLOT01_ROOT_MODE=0

This adapter performs dynamic content analysis and emits truth_score signals.
Violates separation of concerns (interprets + attests) but preserved for
backward compatibility during migration.

DO NOT MODIFY - Will be deprecated after Phase 8 migration complete.
"""

import asyncio
import importlib
import inspect
import time
from typing import Dict, Any, Optional, Type
import logging

# Import from orchestrator contracts
try:
    from orchestrator.contracts import SlotResult
except ImportError:
    # Fallback for testing
    from dataclasses import dataclass

    @dataclass
    class SlotResult:
        status: str
        data: Optional[Dict[str, Any]] = None
        error: Optional[str] = None
        request_id: str = ""
        slot_id: str = "slot1_truth_anchor"
        latency_ms: float = 0.0

logger = logging.getLogger("slot1_legacy_adapter")

# Engine imports -------------------------------------------------------------
try:
    from .truth_anchor_engine import TruthAnchorEngine as BasicTruthAnchorEngine
except ImportError:  # pragma: no cover - defensive
    BasicTruthAnchorEngine = None

try:  # pragma: no cover - optional dependency
    from .enhanced_truth_anchor_engine import TruthAnchorEngine as EnhancedTruthAnchorEngine
except ImportError:  # pragma: no cover - optional dependency
    EnhancedTruthAnchorEngine = None

try:  # pragma: no cover - compatibility shim for tests
    from .core import TruthAnchorEngine as LegacyTruthAnchorEngine  # type: ignore
except ImportError:
    LegacyTruthAnchorEngine = None


def _load_legacy_engine_class() -> Optional[Type]:
    """Dynamically import core TruthAnchorEngine to allow test stubs."""
    try:
        module = importlib.import_module("nova.slots.slot01_truth_anchor.core")
        engine_cls = getattr(module, "TruthAnchorEngine")
        return engine_cls  # type: ignore[return-value]
    except Exception:
        return LegacyTruthAnchorEngine


class _FallbackTruthAnchorEngine:
    """Minimal stub used when real engines are unavailable."""

    async def analyze_content(self, content: str, request_id: str, domain: str):
        return {
            "truth_score": 0.8,
            "anchor_stable": True,
            "anchor_used": domain,
            "timestamp": time.time(),
        }

    def establish_anchor(self, domain: str, facts: list) -> str:
        return domain

    def verify_anchor(self, domain: str) -> dict:
        return {"exists": True, "verified": True, "domain": domain}

    def cleanup(self) -> int:
        return 0


class Slot1LegacyAdapter:
    """Legacy adapter with dynamic content analysis (PRE-ROOT-MODE)."""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.engine = self._build_engine()

        # Performance metrics
        self._total_requests = 0
        self._failed_requests = 0
        self._avg_processing_time = 0.0
        self._lock: Optional[asyncio.Lock] = None
        self._shutdown = False

        logger.info("Slot 1 legacy adapter initialized")

    def _build_engine(self):
        engine_cls = self._select_engine_class()
        kwargs = self._collect_engine_kwargs(engine_cls)
        return engine_cls(**kwargs)

    def _select_engine_class(self) -> Type:
        preferred = (self.config.get("engine") or "auto").lower()

        custom_cls = self.config.get("engine_cls")
        if custom_cls:
            return custom_cls
        legacy_cls = _load_legacy_engine_class()
        if legacy_cls:
            return legacy_cls

        if preferred == "basic" and BasicTruthAnchorEngine:
            return BasicTruthAnchorEngine
        if preferred == "enhanced" and EnhancedTruthAnchorEngine:
            return EnhancedTruthAnchorEngine

        if EnhancedTruthAnchorEngine and preferred in {"auto", "enhanced"}:
            return EnhancedTruthAnchorEngine
        if BasicTruthAnchorEngine:
            return BasicTruthAnchorEngine

        logger.warning("Falling back to stub TruthAnchorEngine implementation")
        return _FallbackTruthAnchorEngine

    def _collect_engine_kwargs(self, engine_cls: Type) -> Dict[str, Any]:
        params = inspect.signature(engine_cls.__init__).parameters
        accepts_var_kw = any(p.kind == inspect.Parameter.VAR_KEYWORD for p in params.values())
        candidates = {
            "cache_max": self.config.get("cache_max", 2048),
            "cache_ttl": self.config.get("cache_ttl", 120.0),
            "stable_threshold": self.config.get("stable_threshold", 0.7),
            "secret_key": self.config.get("secret_key"),
            "storage_path": self.config.get("storage_path"),
            "logger": self.config.get("logger", logger),
        }

        kwargs: Dict[str, Any] = {}
        for key, value in candidates.items():
            if value is None:
                continue
            if key in params or accepts_var_kw:
                kwargs[key] = value
        return kwargs

    async def run(self, payload: dict, *, request_id: str) -> SlotResult:
        """Execute truth analysis with robust error handling (LEGACY BEHAVIOR)."""
        if self._shutdown:
            return SlotResult(
                status="error",
                error="adapter_shutdown",
                request_id=request_id,
                slot_id="slot1_truth_anchor"
            )

        start = time.perf_counter()

        try:
            # Validate payload structure
            if not isinstance(payload, dict):
                return self._make_error_result(
                    "invalid_payload_type", request_id, start, "Payload must be a dictionary"
                )

            # Validate content (optional strict validation)
            content = payload.get("content", "")
            if not content or not isinstance(content, str):
                return self._make_error_result(
                    "invalid_content", request_id, start, "Content must be a non-empty string"
                )

            domain = payload.get("anchor_domain", "nova.core")

            # Execute analysis
            analysis = await self.engine.analyze_content(content, request_id, domain)

            if "error" in analysis:
                return self._make_error_result(
                    "engine_error", request_id, start, analysis["error"]
                )

            # Prepare result data
            slot_data = {
                "truth_score": analysis.get("truth_score", 0.5),
                "anchor_stable": analysis.get("anchor_stable", False),
                "critical": analysis.get("critical", False),
                "anchor_domain": analysis.get("anchor_used", domain),
                "processing_metadata": {
                    "request_timestamp": analysis.get("timestamp", time.time()),
                    "engine_version": analysis.get("version", "unknown")
                },
            }

            return self._make_success_result(request_id, start, slot_data)

        except asyncio.CancelledError:
            await self._update_metrics(start, success=False)
            logger.warning(f"Request {request_id} cancelled")
            raise

        except Exception as e:
            logger.error(f"Request {request_id} failed: {e}", exc_info=True)
            return self._make_error_result(
                "processing_error", request_id, start, str(e)
            )

    async def _update_metrics(self, start: float, success: bool):
        """Update performance metrics safely."""
        elapsed = (time.perf_counter() - start) * 1000

        if self._lock is None:
            self._lock = asyncio.Lock()
        async with self._lock:
            self._total_requests += 1
            if not success:
                self._failed_requests += 1

            # Exponential moving average
            if self._avg_processing_time == 0.0:
                self._avg_processing_time = elapsed
            else:
                alpha = 0.1
                self._avg_processing_time = (
                    alpha * elapsed + (1 - alpha) * self._avg_processing_time
                )

    def _make_success_result(self, request_id: str, start: float, data: dict) -> SlotResult:
        """Create a successful result with metrics update."""
        elapsed = (time.perf_counter() - start) * 1000
        self._safe_metrics_update(start, success=True)

        return SlotResult(
            status="ok",
            data=data,
            request_id=request_id,
            slot_id="slot1_truth_anchor",
            latency_ms=elapsed,
        )

    def _make_error_result(self, error_type: str, request_id: str,
                          start: float, message: str) -> SlotResult:
        """Create an error result with metrics update."""
        elapsed = (time.perf_counter() - start) * 1000
        self._safe_metrics_update(start, success=False)

        return SlotResult(
            status="error",
            error=f"{error_type}:{message}",
            request_id=request_id,
            slot_id="slot1_truth_anchor",
            latency_ms=elapsed,
        )

    # ------------------------------------------------------------------
    # Legacy orchestration helpers (preserved for compatibility tests)
    # ------------------------------------------------------------------
    def establish_anchor(self, domain: str, facts: list[str]) -> str:
        """Proxy for legacy establish_anchor behaviours."""
        if not isinstance(domain, str) or not domain.strip():
            raise ValueError("domain_required")
        if not facts:
            raise ValueError("facts_required")
        impl = getattr(self.engine, "establish_anchor", None)
        if callable(impl):
            return impl(domain, facts)
        raise AttributeError("engine_missing_establish_anchor")

    def verify_anchor(self, domain: str) -> Dict[str, Any]:
        """Proxy for legacy verify_anchor behaviours."""
        if not isinstance(domain, str) or not domain.strip():
            return {"exists": False, "verified": False}
        impl = getattr(self.engine, "verify_anchor", None)
        if not callable(impl):
            return {"exists": False, "verified": False, "error": "engine_missing_verify_anchor"}
        try:
            return impl(domain)
        except Exception as exc:
            return {"exists": False, "verified": False, "error": str(exc)}

    def cleanup_cache(self) -> int:
        """Proxy for cleanup() to keep legacy tests intact."""
        impl = getattr(self.engine, "cleanup", None)
        if callable(impl):
            try:
                return impl()
            except Exception as exc:  # pragma: no cover - defensive
                logger.warning("Legacy cleanup failed: %s", exc)
                return 0
        return 0

    def _safe_metrics_update(self, start: float, success: bool):
        """Safely update metrics without blocking."""
        try:
            if hasattr(asyncio, 'get_running_loop'):
                loop = asyncio.get_running_loop()
                loop.create_task(self._update_metrics(start, success))
        except RuntimeError:
            # No event loop, skip metrics update
            pass

    def get_metrics(self) -> Dict[str, Any]:
        """Get comprehensive performance metrics."""
        total = max(1, self._total_requests)
        success_count = self._total_requests - self._failed_requests

        return {
            "total_requests": self._total_requests,
            "failed_requests": self._failed_requests,
            "success_rate": round(success_count / total, 4),
            "avg_processing_time_ms": round(self._avg_processing_time, 2),
            "success_count": success_count,
            "uptime_seconds": getattr(self, '_uptime', 0),
        }

    async def shutdown(self):
        """Graceful shutdown of the adapter."""
        self._shutdown = True
        logger.info("Slot 1 legacy adapter shutting down")
