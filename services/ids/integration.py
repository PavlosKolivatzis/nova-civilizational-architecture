import json
import logging
import time  # needed for perf_counter
from threading import RLock
from typing import Dict, List, Optional

from config.feature_flags import (
    IDS_ALLOWED_SCOPES,
    IDS_SCHEMA_VALIDATE,
    IDS_STRICT_SCOPE_VALIDATE,
)

from .core import IDSConfig, IDSState, InterpretiveDriftSynthesizer

logger = logging.getLogger("ids")


class IDSIntegrationService:
    def __init__(self) -> None:
        self._lock = RLock()
        self.ids_instances: Dict[str, InterpretiveDriftSynthesizer] = {}
        self.config = IDSConfig()
        self.total_analyses = 0
        self.failed_analyses = 0
        self._consecutive_failures = 0

    def get_analyzer(self, scope: str = "content") -> InterpretiveDriftSynthesizer:
        with self._lock:
            if scope not in self.ids_instances:
                self.ids_instances[scope] = InterpretiveDriftSynthesizer(self.config)
            return self.ids_instances[scope]

    def analyze_vector(
        self,
        vector: List[float],
        previous_vector: Optional[List[float]] = None,
        trace_id: str = "",
        scope: str = "content",
    ) -> Dict:
        start_time = time.perf_counter()
        try:
            if IDS_SCHEMA_VALIDATE:
                self._validate_input(vector, previous_vector, trace_id, scope)

            analyzer = self.get_analyzer(scope)
            result = analyzer.analyze(vector, previous_vector, trace_id, scope)

            with self._lock:
                self.total_analyses += 1
                self._consecutive_failures = 0

            if IDS_SCHEMA_VALIDATE:
                self._validate_output(result)

            log_data = {
                "event": "ids_eval",
                "trace_id": trace_id,
                "slot": "S04",
                "scope": scope,
                "stability": result.get("stability", 0.0),
                "drift": result.get("drift", 0.0),
                "state": result.get("state", "unknown"),
                "vector_length": len(vector),
                "latency_ms": result.get("latency_ms", 0),
                "error": result.get("error"),
            }
            logger.info(json.dumps(log_data))
            return result
        except Exception as e:
            with self._lock:
                self.failed_analyses += 1
                self._consecutive_failures += 1

            if self._consecutive_failures > 50 and self.total_analyses > 1000:
                error_rate = self.failed_analyses / max(1, self.total_analyses)
                if error_rate > 0.05:
                    logger.warning(
                        json.dumps(
                            {
                                "event": "ids_backpressure_triggered",
                                "reason": f"error_rate_{error_rate:.3f}",
                                "consecutive_failures": self._consecutive_failures,
                            }
                        )
                    )

            error_data = {
                "event": "ids_analysis_failed",
                "trace_id": trace_id,
                "scope": scope,
                "error": str(e),
                "vector_length": len(vector) if vector else 0,
                "latency_ms": (time.perf_counter() - start_time) * 1000,
            }
            logger.error(json.dumps(error_data))
            return {
                "stability": 0.0,
                "drift": 0.0,
                "state": IDSState.DISINTEGRATING.value,
                "error": str(e),
                "trace_id": trace_id,
                "scope": scope,
                "latency_ms": (time.perf_counter() - start_time) * 1000,
            }

    def _validate_input(
        self,
        vector: List[float],
        previous_vector: Optional[List[float]],
        trace_id: str,
        scope: str,
    ) -> None:
        if not vector:
            raise ValueError("Empty vector")
        if not isinstance(vector, list):
            raise ValueError("Vector must be a list")
        if not all(isinstance(x, (int, float)) for x in vector):
            raise ValueError("Vector must contain numbers")
        if not trace_id:
            raise ValueError("Missing trace_id")
        allowed = set(IDS_ALLOWED_SCOPES or ["traits", "content", "signals", "memory"])
        if scope not in allowed:
            msg = f"Unknown scope '{scope}' (allowed: {sorted(allowed)})"
            if IDS_STRICT_SCOPE_VALIDATE:
                raise ValueError(msg)
            logger.warning(json.dumps({"event": "ids_scope_warning", "detail": msg}))

    def _validate_output(self, result: Dict) -> None:
        if "stability" not in result or not 0 <= result["stability"] <= 1:
            raise ValueError("Invalid stability value")
        if "drift" not in result or not -1 <= result["drift"] <= 1:
            raise ValueError("Invalid drift value")
        if "state" not in result or result["state"] not in [
            "stable",
            "reintegrating",
            "diverging",
            "disintegrating",
        ]:
            raise ValueError("Invalid state value")

    def get_metrics(self) -> Dict:
        with self._lock:
            metrics = {
                "total_analyses": self.total_analyses,
                "failed_analyses": self.failed_analyses,
                "success_rate": (self.total_analyses - self.failed_analyses)
                / max(1, self.total_analyses),
                "active_scopes": list(self.ids_instances.keys()),
                "scope_instance_count": len(self.ids_instances),
                "consecutive_failures": self._consecutive_failures,
            }
            perf_metrics = {}
            for scope, analyzer in self.ids_instances.items():
                perf_metrics[scope] = analyzer.get_performance_metrics()
            metrics["performance"] = perf_metrics
            return metrics


ids_service = IDSIntegrationService()
