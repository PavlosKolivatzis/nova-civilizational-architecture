"""Slot 2 ΔTHRESH Integration Manager - core processing pipeline."""

import hashlib
import logging
import threading
import time
from typing import Any, Dict, List, Optional, Tuple

from .config import (
    OperationalMode,
    ProcessingConfig,
    ProcessingMode,
    QuarantineReasonCode,
)
from .metrics import PerformanceTracker
from .models import ProcessingResult
from .patterns import PatternDetector


class DeltaThreshProcessor:
    """Production-grade content processor with pattern detection."""

    VERSION = "1.0.0"

    def __init__(
        self,
        config: Optional[ProcessingConfig] = None,
        slot1_anchor_system: Any | None = None,
    ) -> None:
        self.config = config or ProcessingConfig()
        self.anchor_system = slot1_anchor_system

        self.logger = self._setup_logger()
        self.pattern_detector = PatternDetector(self.config)
        self.performance_tracker = PerformanceTracker()
        self._lock = threading.RLock()

        self.logger.info(f"ΔTHRESH Processor v{self.VERSION} initialized")
        self.logger.info(
            f"Operational Mode: {self.config.operational_mode.value}"
        )
        self.logger.info(
            f"Processing Mode: {self.config.processing_mode.value}"
        )

    # ------------------------------------------------------------------
    def _setup_logger(self) -> logging.Logger:
        logger = logging.getLogger("slot2_deltathresh")
        logger.setLevel(logging.INFO)
        if not logger.handlers:
            handler = logging.StreamHandler()
            handler.setFormatter(
                logging.Formatter("%(asctime)s - SLOT2-%(levelname)s - %(message)s")
            )
            logger.addHandler(handler)
        return logger

    # ------------------------------------------------------------------
    def process_content(self, content: str, session_id: str = "default") -> ProcessingResult:
        start_time = time.time()
        with self._lock:
            anchor_integrity = 1.0
            if self.anchor_system:
                try:
                    status = self.anchor_system.validate_anchor_integrity()
                    anchor_integrity = status.get("integrity_score", 1.0)
                    if anchor_integrity < 0.8:
                        self.logger.warning(
                            f"Anchor integrity below threshold: {anchor_integrity:.3f}"
                        )
                except Exception as exc:  # pragma: no cover - defensive
                    self.logger.error(f"Anchor system validation failed: {exc}")

            tri_score = self._calculate_tri_score(content)
            layer_scores = self.pattern_detector.detect_patterns(content)
            action, reason_codes = self._determine_action(
                tri_score, layer_scores, content
            )

            processed_content = content
            neutralized_content = None
            quarantine_reason = None
            if action == "quarantine":
                quarantine_reason = self._generate_quarantine_reason(
                    reason_codes, layer_scores
                )
                self.performance_tracker.record_quarantine()
            elif action == "neutralize":
                neutralized_content = self.pattern_detector.neutralize_patterns(content)
                processed_content = neutralized_content
                self.performance_tracker.record_neutralization()
            else:
                self.performance_tracker.record_allow()

            processing_time_ms = (time.time() - start_time) * 1000
            self.performance_tracker.update_metrics(
                processing_time_ms, reason_codes, layer_scores, tri_score
            )

            result = ProcessingResult(
                content=processed_content,
                action=action,
                reason_codes=reason_codes,
                tri_score=tri_score,
                layer_scores=layer_scores,
                processing_time_ms=processing_time_ms,
                content_hash=hashlib.sha256(content.encode()).hexdigest()[:16],
                neutralized_content=neutralized_content,
                quarantine_reason=quarantine_reason,
                operational_mode=self.config.operational_mode.value,
                session_id=session_id,
                anchor_integrity=anchor_integrity,
            )

            self.logger.debug(
                f"Content processed: {action} (TRI: {tri_score:.3f}, "
                f"Time: {processing_time_ms:.1f}ms)"
            )
            return result

    # ------------------------------------------------------------------
    def _calculate_tri_score(self, content: str) -> float:
        if not self.config.tri_enabled:
            return 1.0
        tri = self.pattern_detector.analyze_tri_patterns(content)
        words = len(content.split())
        if words == 0:
            return 0.5
        absolute_penalty = min(0.4, (tri["absolute_claims"] / words) * 2.0)
        humility_bonus = min(0.3, (tri["humility_indicators"] / words) * 1.5)
        uncertainty_bonus = min(0.2, (tri["uncertainty_acknowledgments"] / words) * 1.0)
        score = 0.7 - absolute_penalty + humility_bonus + uncertainty_bonus
        return max(0.0, min(1.0, score))

    # ------------------------------------------------------------------
    def _determine_action(
        self, tri_score: float, layer_scores: Dict[str, float], content: str
    ) -> Tuple[str, List[str]]:
        reasons: List[str] = []
        if tri_score < self.config.tri_min_score:
            reasons.append(QuarantineReasonCode.TRI_BELOW_MIN.value)
        layer_thresholds = {
            "delta": (
                self.config.thresholds["delta"],
                QuarantineReasonCode.DELTA_SELF_LEGITIMATION,
            ),
            "sigma": (
                self.config.thresholds["sigma"],
                QuarantineReasonCode.SIGMA_ENTROPY_DRIFT,
            ),
            "theta": (
                self.config.thresholds["theta"],
                QuarantineReasonCode.THETA_CIRCULAR_VALIDATION,
            ),
            "omega": (
                self.config.thresholds["omega"],
                QuarantineReasonCode.OMEGA_SOCIAL_PROOF,
            ),
        }
        for name, (thr, code) in layer_thresholds.items():
            if layer_scores.get(name, 0.0) > thr:
                reasons.append(code.value)

        if not reasons:
            return "allow", []

        if self.config.processing_mode == ProcessingMode.QUARANTINE_ONLY:
            return "quarantine", reasons
        elif self.config.processing_mode == ProcessingMode.NEUTRALIZE_PATTERNS:
            if self.config.pattern_neutralization_enabled:
                return "neutralize", reasons
            return "quarantine", reasons
        elif self.config.processing_mode == ProcessingMode.HYBRID_PROCESSING:
            manipulation_score = max(layer_scores.values()) if layer_scores else 0.0
            if manipulation_score > self.config.neutralization_threshold:
                return "quarantine", reasons
            if self.config.pattern_neutralization_enabled:
                return "neutralize", reasons
            return "quarantine", reasons
        return "quarantine", reasons

    # ------------------------------------------------------------------
    def _generate_quarantine_reason(
        self, reason_codes: List[str], layer_scores: Dict[str, float]
    ) -> str:
        if not reason_codes:
            return "Content quarantined due to processing policy"
        primary = reason_codes[0]
        mapping = {
            QuarantineReasonCode.TRI_BELOW_MIN.value:
                "Truth Resonance Index below minimum threshold",
            QuarantineReasonCode.DELTA_SELF_LEGITIMATION.value:
                "Self-legitimating authority patterns detected",
            QuarantineReasonCode.SIGMA_ENTROPY_DRIFT.value:
                "Symbolic manipulation patterns detected",
            QuarantineReasonCode.THETA_CIRCULAR_VALIDATION.value:
                "Circular validation patterns detected",
            QuarantineReasonCode.OMEGA_SOCIAL_PROOF.value:
                "Social proof manipulation patterns detected",
        }
        base = mapping.get(primary, primary)
        if len(reason_codes) > 1:
            return f"{base} (plus {len(reason_codes) - 1} additional concerns)"
        return base

    # ------------------------------------------------------------------
    def sync_with_anchor_system(self, anchor_system: Any) -> Dict[str, Any]:
        self.anchor_system = anchor_system
        if not anchor_system:
            self.logger.warning("No anchor system available for synchronization")
            return {
                "sync_successful": False,
                "error": "No anchor system provided",
                "sync_timestamp": time.time(),
            }
        try:
            anchor_status = anchor_system.get_anchor_status()
            tri_lock = anchor_status.get("tri_lock", 0.9)
            if tri_lock >= 0.95:
                self.config.tri_strict_mode = True
                self.config.tri_min_score = max(0.90, tri_lock - 0.05)
            self.logger.info(
                f"Synchronized with Slot 1: {anchor_status.get('anchor_state')}"
            )
            return {
                "sync_successful": True,
                "anchor_integrity": anchor_status.get("anchor_state"),
                "tri_lock_status": anchor_status.get("tri_lock"),
                "constellation_position": anchor_status.get("constellation_position"),
                "sync_timestamp": time.time(),
            }
        except Exception as exc:  # pragma: no cover - defensive
            self.logger.error(f"Anchor synchronization failed: {exc}")
            return {
                "sync_successful": False,
                "error": str(exc),
                "sync_timestamp": time.time(),
            }

    # ------------------------------------------------------------------
    def get_status(self) -> Dict[str, Any]:
        return {
            "slot_id": 2,
            "slot_name": "ΔTHRESH Integration Manager",
            "version": self.VERSION,
            "operational_mode": self.config.operational_mode.value,
            "processing_mode": self.config.processing_mode.value,
            "integration_active": True,
            "pattern_neutralization": self.config.pattern_neutralization_enabled,
            "tri_enabled": self.config.tri_enabled,
            "tri_min_score": self.config.tri_min_score,
            "performance_metrics": self.performance_tracker.get_metrics(),
            "anchor_system_linked": self.anchor_system is not None,
            "last_update": time.time(),
        }

    # ------------------------------------------------------------------
    def reconfigure_operational_mode(
        self, mode: OperationalMode
    ) -> Dict[str, Any]:
        old_mode = self.config.operational_mode
        try:
            with self._lock:
                self.config.operational_mode = mode
                if mode == OperationalMode.STABLE_LOCK:
                    self.config.tri_strict_mode = True
                    self.config.quarantine_enabled = True
                    self.config.pattern_neutralization_enabled = True
                elif mode == OperationalMode.CANARY_TIGHT:
                    self.config.tri_strict_mode = True
                    self.config.tri_min_score = 0.95
                    self.config.quarantine_enabled = True
                elif mode == OperationalMode.PASS_THROUGH:
                    self.config.tri_strict_mode = False
                    self.config.quarantine_enabled = False
                    self.config.pattern_neutralization_enabled = False
                result = {
                    "reconfiguration_successful": True,
                    "old_mode": old_mode.value,
                    "new_mode": mode.value,
                    "reconfiguration_timestamp": time.time(),
                    "updated_config": {
                        "tri_strict_mode": self.config.tri_strict_mode,
                        "tri_min_score": self.config.tri_min_score,
                        "quarantine_enabled": self.config.quarantine_enabled,
                        "pattern_neutralization_enabled": self.config.pattern_neutralization_enabled,
                    },
                }
                self.logger.info(
                    f"Operational mode changed: {old_mode.value} → {mode.value}"
                )
                return result
        except Exception as exc:  # pragma: no cover - defensive
            self.config.operational_mode = old_mode
            self.logger.error(f"Mode reconfiguration failed: {exc}")
            return {
                "reconfiguration_successful": False,
                "error": str(exc),
                "mode_restored": old_mode.value,
                "reconfiguration_timestamp": time.time(),
            }

    # ------------------------------------------------------------------
    def validate_patterns(self) -> Dict[str, Any]:
        return self.pattern_detector.validate_patterns()

    # ------------------------------------------------------------------
    def get_threat_data_for_slot9(self) -> Dict[str, Any]:
        metrics = self.performance_tracker.get_metrics()
        return {
            "source_slot": 2,
            "timestamp": time.time(),
            "threat_summary": {
                "total_processed": metrics.get("total_processed", 0),
                "quarantine_rate": metrics.get("quarantine_rate", 0.0),
                "neutralization_rate": metrics.get("neutralization_rate", 0.0),
                "avg_tri_score": metrics.get("avg_tri_score", 0.0),
                "manipulation_patterns": metrics.get("reason_code_counts", {}),
                "processing_performance": {
                    "avg_time_ms": metrics.get("avg_processing_time", 0.0),
                    "budget_violations": metrics.get(
                        "layer_latency_violations", 0
                    ),
                },
            },
            "layer_analysis": {
                "delta_detections": metrics.get("layer_detections", {}).get(
                    "delta", 0
                ),
                "sigma_detections": metrics.get("layer_detections", {}).get(
                    "sigma", 0
                ),
                "theta_detections": metrics.get("layer_detections", {}).get(
                    "theta", 0
                ),
                "omega_detections": metrics.get("layer_detections", {}).get(
                    "omega", 0
                ),
            },
            "recommendations": self._generate_threat_recommendations(metrics),
        }

    # ------------------------------------------------------------------
    def _generate_threat_recommendations(self, metrics: Dict[str, Any]) -> List[str]:
        recs: List[str] = []
        if metrics.get("quarantine_rate", 0.0) > 0.1:
            recs.append(
                "High quarantine rate detected - consider tightening upstream filters"
            )
        if metrics.get("neutralization_rate", 0.0) > 0.2:
            recs.append(
                "Frequent pattern neutralization - review content sources"
            )
        if metrics.get("avg_tri_score", 0.0) < 0.7:
            recs.append(
                "Low average TRI scores - implement truth resonance training"
            )
        if metrics.get("avg_processing_time", 0.0) > 40.0:
            recs.append(
                "Processing time approaching budget limits - optimize patterns"
            )
        return recs
