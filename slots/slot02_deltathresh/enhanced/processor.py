"""Enhanced ΔTHRESH processor implementation."""

from __future__ import annotations

import hashlib
import logging
import threading
import time
from typing import Dict, List, Optional, Tuple

from ..core import DeltaThreshProcessor
from ..models import ProcessingResult
from .config import EnhancedProcessingConfig
from .detector import EnhancedPatternDetector
from .performance import EnhancedPerformanceTracker


class EnhancedDeltaThreshProcessor(DeltaThreshProcessor):
    """ΔTHRESH Integration Manager with production enhancements."""

    VERSION = "2.0.0"

    def __init__(
        self,
        config: Optional[EnhancedProcessingConfig] = None,
        slot1_anchor_system=None,
    ) -> None:
        config = config or EnhancedProcessingConfig()
        super().__init__(config=config, slot1_anchor_system=slot1_anchor_system)
        self.config: EnhancedProcessingConfig = config
        self.anchor_system = slot1_anchor_system
        self.pattern_detector = EnhancedPatternDetector(self.config)
        self.performance_tracker = EnhancedPerformanceTracker()
        self._lock = threading.RLock()

        self.logger = logging.getLogger("slot2_deltathresh_enhanced")
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            handler.setFormatter(
                logging.Formatter("%(asctime)s - SLOT2-ENHANCED-%(levelname)s - %(message)s")
            )
            self.logger.addHandler(handler)

    # ------------------------------------------------------------------
    # processing
    # ------------------------------------------------------------------
    def process_content(self, content: str, session_id: str = "default") -> ProcessingResult:
        """Process content with optional pass-through."""

        if not self.config.quarantine_enabled and not self.config.pattern_neutralization_enabled:
            return ProcessingResult(
                content=content,
                action="allow",
                reason_codes=[],
                tri_score=1.0,
                layer_scores={},
                processing_time_ms=0.0,
                content_hash=hashlib.sha256(content.encode()).hexdigest()[:16],
            )

        t0 = time.time()
        tri = self._calculate_enhanced_tri_score(content) if self.config.tri_enabled else 1.0
        layer_scores = self.pattern_detector.detect_patterns_advanced(content)
        action, reasons = self._determine_action(tri, layer_scores)
        processing_time_ms = (time.time() - t0) * 1000
        self.performance_tracker.update_metrics(processing_time_ms, reasons, layer_scores)

        return ProcessingResult(
            content=content,
            action=action,
            reason_codes=reasons,
            tri_score=tri,
            layer_scores=layer_scores,
            processing_time_ms=processing_time_ms,
            content_hash=hashlib.sha256(content.encode()).hexdigest()[:16],
        )

    # ------------------------------------------------------------------
    # internals
    # ------------------------------------------------------------------
    def _calculate_enhanced_tri_score(self, content: str) -> float:
        base = super()._tri_score(content)
        coherence = self.pattern_detector._contextual_consistency(content)
        return max(0.0, min(1.0, base + coherence * 0.05))

    def _determine_action(self, tri: float, layer_scores: Dict[str, float]) -> Tuple[str, List[str]]:
        reasons: List[str] = []
        if tri < self.config.tri_min_score:
            reasons.append("TRI_BELOW_MIN")
        for layer in ["delta", "sigma", "theta", "omega"]:
            threshold = getattr(self.config, f"{layer}_threshold", 1.0)
            if layer_scores.get(layer, 0.0) > threshold:
                reasons.append(f"{layer.upper()}_THRESHOLD_EXCEEDED")
        if not reasons:
            return "allow", []
        return "quarantine", reasons

    # ------------------------------------------------------------------
    # status
    # ------------------------------------------------------------------
    def get_enhanced_status(self) -> Dict[str, Dict]:
        status = self.performance_tracker.get_enhanced_metrics()
        status.update(
            {
                "version": self.VERSION,
                "cache_enabled": self.config.cache_enabled,
                "batch_processing": self.config.batch_processing,
                "adaptive_thresholds": self.config.adaptive_thresholds,
            }
        )
        return status
