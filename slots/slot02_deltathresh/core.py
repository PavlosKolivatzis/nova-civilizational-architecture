import time, hashlib
from typing import Dict, List, Tuple
from .config import ProcessingConfig, ProcessingMode
from .models import ProcessingResult
from .patterns import compile_detection_patterns, ABSOLUTE, HUMILITY, UNCERTAINTY
from .metrics import PerformanceTracker

class DeltaThreshProcessor:
    def __init__(self, config: ProcessingConfig | None = None, anchor=None):
        self.config = config or ProcessingConfig()
        self.anchor = anchor
        self.patterns = compile_detection_patterns()
        self.metrics = PerformanceTracker()

    def process_content(self, content: str, session_id: str = "default") -> ProcessingResult:
        t0 = time.time()

        tri = self._tri_score(content)
        layer_scores = self._layer_scores(content)
        action, reason_codes = self._decide(tri, layer_scores)

        processing_time_ms = (time.time() - t0) * 1000
        self.metrics.update(processing_time_ms, action, reason_codes)

        return ProcessingResult(
            content=content,  # Phase 2 may override with neutralized text
            action=action,
            reason_codes=reason_codes,
            tri_score=tri,
            layer_scores=layer_scores,
            processing_time_ms=processing_time_ms,
            content_hash=hashlib.sha256(content.encode()).hexdigest()[:16],
        )

    # --- internals ---

    def _tri_score(self, content: str) -> float:
        words = max(1, len(content.split()))
        penalty = min(0.4, (len(ABSOLUTE.findall(content)) / words) * 2.0)
        bonus_h = min(0.3, (len(HUMILITY.findall(content)) / words) * 1.5)
        bonus_u = min(0.2, (len(UNCERTAINTY.findall(content)) / words) * 1.0)
        return max(0.0, min(1.0, 0.7 - penalty + bonus_h + bonus_u))

    def _layer_scores(self, content: str) -> Dict[str, float]:
        words = max(1, len(content.split()))
        scores: Dict[str, float] = {}
        for layer, pats in self.patterns.items():
            total = sum(len(p.findall(content)) for p in pats)
            density = total / words
            scores[layer] = min(1.0, density * 5.0)
        return scores

    def _decide(self, tri: float, layer_scores: Dict[str, float]) -> Tuple[str, List[str]]:
        reasons: List[str] = []
        if tri < self.config.tri_min_score:
            reasons.append("TRI_BELOW_MIN")
        for layer, threshold in self.config.thresholds.items():
            if layer_scores.get(layer, 0.0) > threshold:
                reasons.append(f"{layer.upper()}_THRESHOLD_EXCEEDED")

        if not reasons:
            return "allow", []

        # Phase 1: quarantine only (neutralization comes in Phase 2)
        if self.config.processing_mode == ProcessingMode.QUARANTINE_ONLY:
            return "quarantine", reasons
        # For now, keep MVP conservative:
        return "quarantine", reasons
