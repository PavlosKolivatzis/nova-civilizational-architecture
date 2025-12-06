"""Slot 2 ΔTHRESH Integration Manager - core processing pipeline."""

from __future__ import annotations

import hashlib
import logging
import os
import threading
import time
from typing import Any, Dict, List, Mapping, Optional, Tuple, cast

from .config import (
    OperationalMode,
    ProcessingConfig,
    ProcessingMode,
    QuarantineReasonCode,
    FidelityWeightingConfig,
)
from .metrics import PerformanceTracker
from .models import ProcessingResult
from .patterns import PatternDetector, _word_count_fast
from .fidelity_weighting import FidelityWeightingService

# Phase 14.3: USM Bias Detection (feature-gated)
try:
    from .text_graph_parser import TextGraphParser
    from .bias_calculator import BiasCalculator
    _BIAS_DETECTION_AVAILABLE = True
except ImportError:
    _BIAS_DETECTION_AVAILABLE = False


class DeltaThreshProcessor:
    """Production-grade content processor with pattern detection."""

    VERSION = "1.0.0"

    def __init__(
        self,
        config: Optional[ProcessingConfig] = None,
        slot1_anchor_system: Optional[Any] = None,
    ) -> None:
        self.config = config or ProcessingConfig()
        self.anchor_system = slot1_anchor_system

        self.logger = self._setup_logger()
        self.pattern_detector = PatternDetector(self.config)
        self.performance_tracker = PerformanceTracker()
        self._lock = threading.RLock()
        self._fidelity_service = None
        if hasattr(self.config, "fidelity_weighting"):
            self._fidelity_service = FidelityWeightingService(self.config.fidelity_weighting)
        self._last_fidelity_weight = 1.0

        # Phase 14.3: Bias detection (feature-gated)
        self._bias_detection_enabled = (
            os.getenv('NOVA_ENABLE_BIAS_DETECTION', '0') == '1' and
            _BIAS_DETECTION_AVAILABLE
        )
        self._text_parser = None
        self._bias_calculator = None
        if self._bias_detection_enabled:
            self._text_parser = TextGraphParser(enable_logging=False)
            self._bias_calculator = BiasCalculator()
            self.logger.info("USM Bias Detection: ENABLED")
        else:
            self.logger.info("USM Bias Detection: DISABLED")

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
            tri_score, layer_scores, fidelity_weight = self._apply_fidelity_weighting(tri_score, layer_scores)
            self._last_fidelity_weight = fidelity_weight
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
            elif action == "allow" and reason_codes:
                self.performance_tracker.record_pass_through_breach()
            else:
                self.performance_tracker.record_allow()

            processing_time_ms = (time.time() - start_time) * 1000
            self.performance_tracker.update_metrics(
                processing_time_ms, reason_codes, layer_scores, tri_score
            )

            # Phase 14.3: Bias detection (if enabled)
            bias_report = None
            if self._bias_detection_enabled:
                try:
                    bias_report = self._analyze_bias(content)
                except Exception as exc:
                    self.logger.warning(f"Bias detection failed: {exc}")

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
                bias_report=bias_report,
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
        words = max(1, _word_count_fast(content))
        absolute_penalty = min(0.4, (tri["absolute_claims"] / words) * 2.0)
        humility_bonus = min(0.3, (tri["humility_indicators"] / words) * 1.5)
        uncertainty_bonus = min(0.2, (tri["uncertainty_acknowledgments"] / words) * 1.0)
        score = 0.7 - absolute_penalty + humility_bonus + uncertainty_bonus
        return max(0.0, min(1.0, score))

    def _apply_fidelity_weighting(
        self, tri_score: float, layer_scores: Dict[str, float]
    ) -> Tuple[float, Dict[str, float], float]:
        config = getattr(self.config, "fidelity_weighting", None)
        if (
            not config
            or not getattr(config, "enabled", False)
            or self._fidelity_service is None
        ):
            return tri_score, layer_scores, 1.0

        weight, _sample = self._fidelity_service.compute_weight()
        if weight == 1.0:
            return tri_score, layer_scores, weight

        adjusted_tri = max(0.0, min(1.0, tri_score * weight))
        inv = 1.0 / weight if weight else 1.0
        adjusted_layers = {
            name: max(0.0, min(1.0, score * inv))
            for name, score in layer_scores.items()
        }
        return adjusted_tri, adjusted_layers, weight

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
            # No breaches → allow as usual
            return "allow", []

        # --- PASS-THROUGH GUARD ---
        # Honor reconfigure_operational_mode() when quarantine is disabled.
        # We check both runtime and config for maximum compatibility.
        quarantine_enabled = getattr(
            getattr(self, "runtime", self.config), "quarantine_enabled", True
        )
        if (
            self.config.operational_mode == OperationalMode.PASS_THROUGH
            or not quarantine_enabled
        ):
            # In pass-through we still return reasons for logging/metrics
            # but we never quarantine or neutralize.
            return "allow", reasons

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
        metrics: Dict[str, Any] = self.performance_tracker.get_metrics()
        layer_detections_raw = metrics.get("layer_detections", {})
        if isinstance(layer_detections_raw, Mapping):
            layer_detections = cast(Mapping[str, Any], layer_detections_raw)
        else:
            layer_detections = {}
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
                "delta_detections": int(layer_detections.get("delta", 0)),
                "sigma_detections": int(layer_detections.get("sigma", 0)),
                "theta_detections": int(layer_detections.get("theta", 0)),
                "omega_detections": int(layer_detections.get("omega", 0)),
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

    # ------------------------------------------------------------------
    # Phase 14.3: USM Bias Detection
    # ------------------------------------------------------------------
    def _analyze_bias(self, content: str) -> Dict[str, Any]:
        """
        Analyze input text for cognitive bias patterns using USM.

        Args:
            content: Input text to analyze

        Returns:
            BIAS_REPORT@1 contract dict

        Raises:
            Exception: If parsing or analysis fails
        """
        if not self._bias_detection_enabled:
            return None

        # Parse text → SystemGraph
        graph = self._text_parser.parse(content)

        # Analyze graph → BiasReport
        report = self._bias_calculator.analyze_text_graph(graph, enable_logging=False)

        # Convert to BIAS_REPORT@1 contract format
        bias_report = {
            'bias_vector': report.bias_vector,
            'collapse_score': report.collapse_score,
            'usm_metrics': report.usm_metrics,
            'metadata': {
                **report.metadata,
                'text_length': len(content),
                'timestamp': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())
            },
            'confidence': report.confidence
        }

        return bias_report
