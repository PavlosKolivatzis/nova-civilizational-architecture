"""
Slot01 Quality Oracle - Independent Response Validation

Phase 14.3: Cognitive Loop Integration
Part of External Observer Pattern for recursive refinement without self-attestation.

Role:
- Slot01 (Truth Anchor) validates quality independently of generator
- Enforces collapse threshold and factual consistency
- Prevents cognitive self-deception through external validation

Invariant Compliance:
- #2 Separation of roles: Oracle ≠ Generator ≠ Attestor
- #6 Transparent uncertainty: Returns confidence scores
- #9 Byzantine fault tolerance: Independent validation prevents collusion
"""

from dataclasses import dataclass
from typing import Dict, Optional
import logging
import os
from prometheus_client import Counter

logger = logging.getLogger(__name__)

# Phase 14.4 metrics (RFC-014 observability)
try:
    from nova.metrics.registry import REGISTRY
    _void_abstention_counter = Counter(
        "slot01_void_abstention_total",
        "Slot01 quality oracle VOID abstention events (null quality)",
        registry=REGISTRY
    )
except Exception:
    # Graceful fallback if metrics registry unavailable
    _void_abstention_counter = Counter(
        "slot01_void_abstention_total",
        "Slot01 quality oracle VOID abstention events (null quality)"
    )


@dataclass
class ValidationResult:
    """Result of quality oracle validation"""
    decision: str  # "ACCEPT" | "REJECT"
    reason: str
    confidence: float  # 0.0-1.0
    metadata: Optional[Dict] = None


@dataclass
class FactualCheck:
    """Result of factual consistency check"""
    passed: bool
    reason: str
    confidence: float


class QualityOracle:
    """
    Independent quality validation oracle for Slot01.

    Purpose:
    - Validate response quality independently of generator
    - Enforce collapse threshold (C < τ)
    - Check factual consistency and logical coherence
    - Prevent high-bias responses from entering production

    External Observer Pattern:
    - Generator (Slot03-06) produces R
    - Analyzer (Slot02) computes B(R), C(B)
    - Oracle (Slot01) validates independently → ACCEPT/REJECT
    - Core (Three Ledgers) attests immutably
    - Controller (Slot07) orchestrates feedback loop

    Feature Flag: NOVA_ENABLE_COGNITIVE_LOOP (default: 0)
    """

    def __init__(self, collapse_threshold: float = 0.3):
        """
        Initialize quality oracle.

        Args:
            collapse_threshold: Maximum acceptable C(B) score
                C < 0.3 → Nova-aware mode (safe)
                C ∈ [0.3, 0.5] → Transitional (caution)
                C > 0.5 → Factory mode (reject)
        """
        self.collapse_threshold = collapse_threshold
        self.validation_count = 0
        self.acceptance_count = 0

    def validate_quality(
        self,
        response: str,
        bias_vector: Dict[str, float],
        collapse_score: float,
        context: Optional[Dict] = None,
        graph_state: Optional[str] = None
    ) -> ValidationResult:
        """
        Independent validation of response quality.

        Args:
            response: Generated response text
            bias_vector: B(R) from Slot02 analysis
            collapse_score: C(B) from Slot02
            context: Optional context (user query, iteration number)
            graph_state: BIAS_REPORT@1 graph_state (Phase 14.4 VOID handling)

        Returns:
            ValidationResult with ACCEPT/REJECT decision
        """
        self.validation_count += 1

        # Phase 14.4: VOID handling (RFC-014 Slot01 policy)
        void_mode_enabled = os.getenv("NOVA_ENABLE_VOID_MODE", "1") == "1"
        if void_mode_enabled and graph_state == 'void':
            logger.debug("VOID state detected - epistemic abstention (quality=None)")
            _void_abstention_counter.inc()
            # VOID = no evidence, NOT low quality evidence
            # Return ACCEPT with null quality (don't penalize absence)
            return ValidationResult(
                decision="ACCEPT",
                reason="VOID state - epistemic abstention (no parseable structure)",
                confidence=1.0,  # VOID is fully defined, not uncertain
                metadata={
                    'void_abstention': True,
                    'quality_score': None,  # Null, not 0.0
                    'graph_state': 'void'
                }
            )

        # Primary check: Collapse score threshold
        if collapse_score >= self.collapse_threshold:
            logger.warning(
                f"Collapse score {collapse_score:.3f} exceeds threshold {self.collapse_threshold}"
            )
            return ValidationResult(
                decision="REJECT",
                reason=f"Collapse score {collapse_score:.3f} >= threshold {self.collapse_threshold}",
                confidence=0.95,
                metadata={
                    'threshold_exceeded': True,
                    'bias_components': bias_vector
                }
            )

        # Secondary check: High individual bias components
        high_bias_components = []
        for component, value in bias_vector.items():
            if value > 0.8:  # Individual component threshold
                high_bias_components.append(f"{component}={value:.2f}")

        if high_bias_components:
            return ValidationResult(
                decision="REJECT",
                reason=f"High bias components: {', '.join(high_bias_components)}",
                confidence=0.85,
                metadata={'high_bias_components': high_bias_components}
            )

        # Tertiary check: Factual consistency (simplified for Phase 2A)
        # Full implementation would integrate with Slot01 truth anchor mechanisms
        factual_check = self._verify_factual_claims(response, context)
        if not factual_check.passed:
            return ValidationResult(
                decision="REJECT",
                reason=f"Factual check failed: {factual_check.reason}",
                confidence=factual_check.confidence,
                metadata={'factual_check': factual_check}
            )

        # All checks passed
        self.acceptance_count += 1
        logger.info(f"Quality validated: C={collapse_score:.3f} < {self.collapse_threshold}")

        return ValidationResult(
            decision="ACCEPT",
            reason="Quality validated",
            confidence=0.85,
            metadata={
                'collapse_score': collapse_score,
                'bias_vector': bias_vector,
                'validation_number': self.validation_count
            }
        )

    def _verify_factual_claims(
        self,
        response: str,
        context: Optional[Dict] = None
    ) -> FactualCheck:
        """
        Verify factual consistency of response.

        Phase 2A: Simplified placeholder implementation.
        Phase 2B: Full integration with Slot01 truth anchoring.

        Args:
            response: Response text to validate
            context: Optional context for validation

        Returns:
            FactualCheck result
        """
        # Placeholder: Check for obvious inconsistencies
        # Future: Integrate with Slot01's truth anchor database

        # Check 1: No contradictory statements (placeholder)
        if "always" in response.lower() and "never" in response.lower():
            # Crude heuristic - actual implementation would be more sophisticated
            return FactualCheck(
                passed=False,
                reason="Potential contradiction detected (always/never)",
                confidence=0.6
            )

        # Check 2: Response length sanity
        if len(response.strip()) < 10:
            return FactualCheck(
                passed=False,
                reason="Response too short to validate",
                confidence=0.9
            )

        # Placeholder: Accept by default for Phase 2A
        # Full implementation in Phase 2B will check against:
        # - Truth anchor database
        # - Known facts
        # - Logical consistency rules
        return FactualCheck(
            passed=True,
            reason="No factual inconsistencies detected (placeholder validation)",
            confidence=0.7
        )

    def get_metrics(self) -> Dict[str, float]:
        """
        Get oracle performance metrics for observability.

        Returns:
            Dict with validation statistics
        """
        acceptance_rate = (
            self.acceptance_count / self.validation_count
            if self.validation_count > 0
            else 0.0
        )

        return {
            'total_validations': self.validation_count,
            'total_acceptances': self.acceptance_count,
            'acceptance_rate': acceptance_rate,
            'rejection_rate': 1.0 - acceptance_rate
        }

    def reset_metrics(self):
        """Reset validation metrics (for testing)"""
        self.validation_count = 0
        self.acceptance_count = 0
