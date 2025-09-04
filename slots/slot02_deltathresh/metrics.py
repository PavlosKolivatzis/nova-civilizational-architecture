from collections import defaultdict
from typing import Dict, List


class PerformanceTracker:
    """Track processing outcomes and performance metrics."""

    def __init__(self) -> None:
        self.total_processed = 0
        self.allowed = 0
        self.quarantined = 0
        self.neutralized = 0
        self.reason_code_counts: Dict[str, int] = defaultdict(int)
        self.layer_detections: Dict[str, int] = defaultdict(int)
        self.avg_processing_time = 0.0
        self.avg_tri_score = 0.0
        self.layer_latency_violations = 0

    # -- action accounting -------------------------------------------------
    def record_allow(self) -> None:
        self.allowed += 1

    def record_quarantine(self) -> None:
        self.quarantined += 1

    def record_neutralization(self) -> None:
        self.neutralized += 1

    # -- metrics -----------------------------------------------------------
    def update_metrics(
        self,
        processing_time_ms: float,
        reason_codes: List[str],
        layer_scores: Dict[str, float],
        tri_score: float | None = None,
    ) -> None:
        self.total_processed += 1
        for code in reason_codes or []:
            self.reason_code_counts[code] += 1
        for layer, score in layer_scores.items():
            if score > 0:
                self.layer_detections[layer] += 1
        n = self.total_processed
        self.avg_processing_time = ((self.avg_processing_time * (n - 1)) + processing_time_ms) / n
        if tri_score is not None:
            self.avg_tri_score = ((self.avg_tri_score * (n - 1)) + tri_score) / n

    # -- reporting ---------------------------------------------------------
    def get_metrics(self) -> Dict[str, float | int | Dict[str, int]]:
        total = self.total_processed or 1
        return {
            "total_processed": self.total_processed,
            "quarantine_rate": self.quarantined / total,
            "neutralization_rate": self.neutralized / total,
            "avg_tri_score": self.avg_tri_score,
            "reason_code_counts": dict(self.reason_code_counts),
            "layer_detections": dict(self.layer_detections),
            "avg_processing_time": self.avg_processing_time,
            "layer_latency_violations": self.layer_latency_violations,
        }
