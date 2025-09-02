import time
import numpy as np
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import threading
import json


class IDSState(str, Enum):
    STABLE = "stable"
    REINTEGRATING = "reintegrating"
    DIVERGING = "diverging"
    DISINTEGRATING = "disintegrating"


@dataclass
class IDSConfig:
    alpha: float = 0.9  # Stability smoothing
    beta: float = 0.8   # Drift sensitivity
    ema_lambda: float = 0.7  # EMA smoothing factor
    stability_thresholds: Dict[IDSState, float] = None

    def __post_init__(self) -> None:
        if self.stability_thresholds is None:
            self.stability_thresholds = {
                IDSState.STABLE: 0.75,
                IDSState.REINTEGRATING: 0.5,
                IDSState.DIVERGING: 0.25,
                IDSState.DISINTEGRATING: 0.0,
            }


class InterpretiveDriftSynthesizer:
    def __init__(self, config: Optional[IDSConfig] = None) -> None:
        self.config = config or IDSConfig()
        self._history: Dict[Tuple[str, str], list] = {}
        self._ema: Dict[Tuple[str, str], float] = {}
        self._lock = threading.RLock()
        self._latency_history: List[float] = []

    def calculate_stability(self, vector: List[float]) -> float:
        """Calculate stability score 0-1 based on vector coherence"""
        if len(vector) < 2:
            return 0.0

        v = np.array(vector, dtype=float)
        nrm = np.linalg.norm(v)
        if nrm < 1e-12:
            return 0.0

        v /= nrm
        entropy = self._calculate_entropy(v)
        consistency = self._calculate_consistency(v)
        stability = self.config.alpha * consistency + (1 - self.config.alpha) * (1 - entropy)
        return float(np.clip(stability, 0.0, 1.0))

    def calculate_drift(self, current_vector: List[float], previous_vector: List[float]) -> float:
        """Calculate drift score -1 to 1 with proper radial direction"""
        if len(current_vector) != len(previous_vector):
            raise ValueError("E_DIMENSION_MISMATCH")

        c = np.array(current_vector, dtype=float)
        p = np.array(previous_vector, dtype=float)
        cn, pn = np.linalg.norm(c), np.linalg.norm(p)
        if cn < 1e-12 and pn < 1e-12:
            return 0.0
        if cn < 1e-12 or pn < 1e-12:
            return float(np.sign(cn - pn))

        c /= cn
        p /= pn
        sim = float(np.dot(c, p))
        angular = (1.0 - sim) / 2.0
        delta = c - p
        radial = float(np.dot(delta, p))
        sign = 1.0 if radial >= 0 else -1.0
        drift = self.config.beta * 4.0 * angular * sign
        return float(np.clip(drift, -1.0, 1.0))

    def analyze(
        self,
        vector: List[float],
        previous_vector: Optional[List[float]] = None,
        trace_id: str = "",
        scope: str = "content",
    ) -> Dict:
        """Main analysis method with proper EMA per key and performance tracking"""
        start_time = time.perf_counter()

        stability = self.calculate_stability(vector)
        drift = 0.0
        error = None
        if previous_vector is not None:
            try:
                drift = self.calculate_drift(vector, previous_vector)
            except ValueError as e:
                error = str(e)
                stability = 0.0
                drift = 0.0

        key = (trace_id, scope)
        with self._lock:
            ema_prev = self._ema.get(key)
            if ema_prev is not None:
                stability = self.config.ema_lambda * stability + (1 - self.config.ema_lambda) * ema_prev
            self._ema[key] = stability

            state = self._determine_state(stability)
            history = self._history.setdefault(key, [])
            history.append({
                "state": state,
                "stability": stability,
                "drift": drift,
                "timestamp": time.time(),
            })
            if len(history) > 100:
                self._history[key] = history[-100:]

        latency_ms = (time.perf_counter() - start_time) * 1000
        self._record_latency(latency_ms)

        result = {
            "stability": stability,
            "drift": drift,
            "state": state.value,
            "trace_id": trace_id,
            "scope": scope,
            "vector_length": len(vector),
            "timestamp": time.time(),
            "latency_ms": latency_ms,
        }
        if error:
            result["error"] = error
        return result

    def _record_latency(self, latency_ms: float) -> None:
        with self._lock:
            self._latency_history.append(latency_ms)
            if len(self._latency_history) > 1000:
                self._latency_history = self._latency_history[-1000:]

    def get_performance_metrics(self) -> Dict:
        with self._lock:
            if not self._latency_history:
                return {"count": 0, "p50": 0, "p95": 0, "p99": 0}
            sorted_latencies = sorted(self._latency_history)
            n = len(sorted_latencies)
            return {
                "count": n,
                "p50": sorted_latencies[int(n * 0.5)],
                "p95": sorted_latencies[int(n * 0.95)],
                "p99": sorted_latencies[int(n * 0.99)],
                "max": sorted_latencies[-1],
            }

    def _determine_state(self, stability: float) -> IDSState:
        if stability >= self.config.stability_thresholds[IDSState.STABLE]:
            return IDSState.STABLE
        if stability >= self.config.stability_thresholds[IDSState.REINTEGRATING]:
            return IDSState.REINTEGRATING
        if stability >= self.config.stability_thresholds[IDSState.DIVERGING]:
            return IDSState.DIVERGING
        return IDSState.DISINTEGRATING

    def _calculate_entropy(self, vector: np.ndarray) -> float:
        n = len(vector)
        if n <= 1:
            return 0.0
        abs_vector = np.abs(vector)
        if np.sum(abs_vector) == 0:
            return 1.0
        probabilities = abs_vector / np.sum(abs_vector)
        entropy = -np.sum(probabilities * np.log(probabilities + 1e-10))
        return float(np.clip(entropy / np.log(n), 0.0, 1.0))

    def _calculate_consistency(self, vector: np.ndarray) -> float:
        if len(vector) < 2:
            return 1.0
        m = float(np.mean(np.abs(vector)))
        if m < 1e-10:
            return 0.0
        std_dev = float(np.std(vector))
        consistency = 1.0 - (std_dev / m)
        return float(np.clip(consistency, 0.0, 1.0))

    def get_history(self, trace_id: str, scope: str = "content") -> List[Dict]:
        key = (trace_id, scope)
        with self._lock:
            return self._history.get(key, [])

    def clear_history(self, trace_id: str, scope: str = "content") -> None:
        key = (trace_id, scope)
        with self._lock:
            if key in self._history:
                del self._history[key]
            if key in self._ema:
                del self._ema[key]
