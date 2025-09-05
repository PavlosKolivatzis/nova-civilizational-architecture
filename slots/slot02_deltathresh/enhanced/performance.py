"""Enhanced performance tracking and anomaly detection."""

from __future__ import annotations

import time
import threading
from collections import defaultdict, deque
from typing import Any, Dict, List

import numpy as np


class AnomalyDetector:
    """Detect simple anomalies based on processing time."""

    def __init__(self, window_size: int = 100):
        self.window = deque(maxlen=window_size)
        self.anomalies: List[Dict[str, float]] = []
        self._lock = threading.RLock()

    def analyze(self, value: float) -> None:
        with self._lock:
            self.window.append(value)
            if len(self.window) < 10:
                return
            arr = np.array(self.window)
            mean = arr.mean()
            std = arr.std()
            if std > 0 and abs(value - mean) > 3 * std:
                self.anomalies.append({
                    "timestamp": time.time(),
                    "value": value,
                    "mean": mean,
                    "std": std,
                })

    def get_anomalies(self) -> List[Dict[str, float]]:
        with self._lock:
            return list(self.anomalies[-10:])


class EnhancedPerformanceTracker:
    """Collect runtime metrics for the enhanced processor."""

    def __init__(self) -> None:
        self.metrics: Dict[str, Any] = {
            "total_processed": 0,
            "quarantine_count": 0,
            "neutralization_count": 0,
            "allow_count": 0,
            "pass_through_breach_count": 0,
            # track TRI scores for compatibility with the core tracker
            "tri_score_sum": 0.0,
            "tri_score_count": 0,
            "processing_times": deque(maxlen=1000),
            "layer_detections": defaultdict(int),
            "reason_code_counts": defaultdict(int),
            # latency violations are not currently tracked but the field is
            # kept for structural compatibility with the core metrics API
            "layer_latency_violations": 0,
            "start_time": time.time(),
        }
        self._lock = threading.RLock()
        self.anomaly_detector = AnomalyDetector()

    def update_metrics(
        self,
        processing_time_ms: float,
        reason_codes: List[str],
        layer_scores: Dict[str, float],
        tri_score: float | None = None,
    ) -> None:
        with self._lock:
            self.metrics["total_processed"] += 1
            self.metrics["processing_times"].append(processing_time_ms)
            for code in reason_codes or []:
                self.metrics["reason_code_counts"][code] += 1
            for layer, score in layer_scores.items():
                if score > 0.3:
                    self.metrics["layer_detections"][layer] += 1
            if tri_score is not None:
                self.metrics["tri_score_sum"] += tri_score
                self.metrics["tri_score_count"] += 1
            self.anomaly_detector.analyze(processing_time_ms)

    # -- compatibility helpers --------------------------------------------
    def record_allow(self) -> None:
        with self._lock:
            self.metrics["allow_count"] += 1

    def record_quarantine(self) -> None:
        with self._lock:
            self.metrics["quarantine_count"] += 1

    def record_neutralization(self) -> None:
        with self._lock:
            self.metrics["neutralization_count"] += 1

    def record_pass_through_breach(self) -> None:
        with self._lock:
            self.metrics["pass_through_breach_count"] += 1

    def get_enhanced_metrics(self) -> Dict[str, Any]:
        with self._lock:
            times = list(self.metrics["processing_times"])
            return {
                "basic": {
                    "total_processed": self.metrics["total_processed"],
                    "quarantine_rate": self.metrics["quarantine_count"] / max(1, self.metrics["total_processed"]),
                    "allow_rate": self.metrics["allow_count"] / max(1, self.metrics["total_processed"]),
                    "neutralization_rate": self.metrics["neutralization_count"] / max(1, self.metrics["total_processed"]),
                    "pass_through_breaches": self.metrics["pass_through_breach_count"],
                },
                "performance": {
                    "avg_processing_time": float(np.mean(times)) if times else 0.0,
                    "p95_processing_time": float(np.percentile(times, 95)) if times else 0.0,
                    "processing_time_std": float(np.std(times)) if times else 0.0,
                },
                "patterns": dict(self.metrics["layer_detections"]),
                "reasons": dict(self.metrics["reason_code_counts"]),
                "anomalies": self.anomaly_detector.get_anomalies(),
                "uptime_seconds": time.time() - self.metrics["start_time"],
            }

    def get_metrics(self) -> Dict[str, Any]:
        """Return a flat metrics structure compatible with the core tracker."""
        with self._lock:
            total = self.metrics["total_processed"] or 1
            times = list(self.metrics["processing_times"])
            avg_time = float(np.mean(times)) if times else 0.0
            avg_tri = (
                self.metrics["tri_score_sum"] / self.metrics["tri_score_count"]
                if self.metrics["tri_score_count"]
                else 0.0
            )
            return {
                "total_processed": self.metrics["total_processed"],
                "quarantine_rate": self.metrics["quarantine_count"] / total,
                "neutralization_rate": self.metrics["neutralization_count"] / total,
                "pass_through_breaches": self.metrics["pass_through_breach_count"],
                "avg_tri_score": avg_tri,
                "reason_code_counts": dict(self.metrics["reason_code_counts"]),
                "layer_detections": dict(self.metrics["layer_detections"]),
                "avg_processing_time": avg_time,
                "layer_latency_violations": self.metrics["layer_latency_violations"],
            }
