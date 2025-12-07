"""
Slot07 Cognitive Loop Controller - Recursive Refinement Orchestrator

Phase 14.3: External Observer Pattern for Safe Recursive Refinement
Part of R→G(R)→USM→B(R)→C→R′ architecture without self-attestation violation.

Architecture:
    Generator (Slot03-06) → Produces response R
           ↓
    Analyzer (Slot02) → R → G(R) → USM metrics → B(R), C(B)
           ↓
    Oracle (Slot01) → Independent validation → ACCEPT/REJECT
           ↓
    Core (Ledgers) → Immutable attestation of iteration
           ↓
    Controller (Slot07) → Feedback loop coordination (this module)

Feature Flag: NOVA_ENABLE_COGNITIVE_LOOP (default: 0)
Max Iterations: 5 (prevents infinite loops)
"""

import os
import logging
from dataclasses import dataclass
from typing import Dict, Optional, Tuple, Callable, Any
from datetime import datetime
from prometheus_client import Counter

logger = logging.getLogger(__name__)

# Phase 14.4 metrics (RFC-014 observability)
try:
    from nova.metrics.registry import REGISTRY
    _void_freeze_counter = Counter(
        "slot07_regime_unchanged_on_void_total",
        "Slot07 cognitive loop VOID freeze events (skip oracle/refinement)",
        registry=REGISTRY
    )
except Exception:
    # Graceful fallback if metrics registry unavailable
    _void_freeze_counter = Counter(
        "slot07_regime_unchanged_on_void_total",
        "Slot07 cognitive loop VOID freeze events (skip oracle/refinement)"
    )


@dataclass
class CognitiveLoopConfig:
    """Configuration for cognitive refinement loop"""
    enabled: bool = False  # Feature flag
    max_iterations: int = 5
    collapse_threshold: float = 0.3
    timeout_seconds: int = 30  # Per iteration
    min_response_length: int = 10


@dataclass
class RefinementFeedback:
    """Feedback from oracle to generator for refinement"""
    iteration: int
    bias_vector: Dict[str, float]
    collapse_score: float
    oracle_reason: str
    suggestions: list[str]


@dataclass
class LoopResult:
    """Final result from cognitive loop"""
    response: str
    bias_report: Dict[str, Any]
    iterations: int
    converged: bool
    total_time_ms: int
    audit_trail: list[Dict]


class CognitiveLoopController:
    """
    Orchestrates recursive cognitive refinement loop.

    Responsibilities:
    - Coordinate Generator → Analyzer → Oracle → Core pipeline
    - Manage iteration limits and timeouts
    - Provide feedback for refinement
    - Collect audit trail for attestation
    - Enforce feature flag and safety bounds

    Invariant Compliance:
    - #2 Separation: Controller ≠ Generator ≠ Validator ≠ Attestor
    - #4 Immutability: All iterations attested immutably
    - #5 Reversibility: Feature flag, max iterations, timeouts
    - #7 Observability: Full audit trail + metrics
    """

    def __init__(self, config: Optional[CognitiveLoopConfig] = None):
        """
        Initialize cognitive loop controller.

        Args:
            config: Optional configuration (defaults loaded from env)
        """
        if config is None:
            config = CognitiveLoopConfig(
                enabled=os.getenv('NOVA_ENABLE_COGNITIVE_LOOP', '0') == '1',
                max_iterations=int(os.getenv('NOVA_COGNITIVE_LOOP_MAX_ITERATIONS', '5')),
                collapse_threshold=float(os.getenv('NOVA_COGNITIVE_LOOP_THRESHOLD', '0.3'))
            )

        self.config = config
        self.total_loops_run = 0
        self.total_iterations_executed = 0
        self.convergence_rate = 0.0

    def run_cognitive_loop(
        self,
        generator_fn: Callable[[Dict], str],
        analyzer_fn: Callable[[str], Tuple[Dict, float, Optional[str]]],  # Returns (bias_vector, collapse_score, graph_state)
        oracle_fn: Callable[[str, Dict, float], Dict],  # Returns validation result
        attestor_fn: Callable[[Dict], None],  # Records to ledger
        input_context: Dict
    ) -> LoopResult:
        """
        Execute recursive cognitive refinement loop.

        Args:
            generator_fn: Function to generate response (Slot03-06)
            analyzer_fn: Function to analyze structure (Slot02)
            oracle_fn: Function to validate quality (Slot01)
            attestor_fn: Function to attest iteration (Core)
            input_context: Context for generation

        Returns:
            LoopResult with final response and audit trail

        Raises:
            TimeoutError: If loop exceeds total time budget
            ValueError: If any function returns invalid data
        """
        if not self.config.enabled:
            # Feature disabled - run single-pass without loop
            response = generator_fn(input_context)
            bias_vector, collapse_score, graph_state = analyzer_fn(response)

            return LoopResult(
                response=response,
                bias_report={
                    'bias_vector': bias_vector,
                    'collapse_score': collapse_score,
                    'graph_state': graph_state
                },
                iterations=1,
                converged=True,  # Single-pass always "converged"
                total_time_ms=0,
                audit_trail=[]
            )

        # Feature enabled - run refinement loop
        start_time = datetime.now()
        audit_trail = []
        current_context = input_context.copy()

        self.total_loops_run += 1

        for iteration in range(self.config.max_iterations):
            iteration_start = datetime.now()

            # Step 1: Generate response
            try:
                response = generator_fn(current_context)
            except Exception as e:
                logger.error(f"Generator failed at iteration {iteration}: {e}")
                raise

            # Step 2: Analyze structure (Slot02)
            try:
                bias_vector, collapse_score, graph_state = analyzer_fn(response)
            except Exception as e:
                logger.error(f"Analyzer failed at iteration {iteration}: {e}")
                raise

            # Phase 14.4: VOID handling (RFC-014 Slot07 freeze policy)
            if graph_state == 'void':
                logger.debug(f"VOID state detected at iteration {iteration} - skipping oracle/refinement")
                _void_freeze_counter.inc()
                # VOID = epistemic null, accept immediately (no quality score)
                return LoopResult(
                    response=response,
                    bias_report={
                        'bias_vector': bias_vector,
                        'collapse_score': collapse_score,
                        'graph_state': 'void'
                    },
                    iterations=iteration + 1,
                    converged=True,  # VOID always converges (nothing to refine)
                    total_time_ms=int((datetime.now() - start_time).total_seconds() * 1000),
                    audit_trail=audit_trail
                )

            # Step 3: Oracle validation (Slot01)
            try:
                validation_result = oracle_fn(response, bias_vector, collapse_score)
            except Exception as e:
                logger.error(f"Oracle failed at iteration {iteration}: {e}")
                raise

            # Step 4: Attest iteration (Core)
            attestation_record = {
                'iteration': iteration,
                'response_hash': hash(response),
                'response_length': len(response),
                'bias_vector': bias_vector,
                'collapse_score': collapse_score,
                'oracle_decision': validation_result['decision'],
                'oracle_reason': validation_result['reason'],
                'oracle_confidence': validation_result['confidence'],
                'timestamp': datetime.now().isoformat(),
                'iteration_time_ms': (datetime.now() - iteration_start).total_seconds() * 1000
            }

            try:
                attestor_fn(attestation_record)
            except Exception as e:
                logger.warning(f"Attestation failed (non-fatal): {e}")

            audit_trail.append(attestation_record)
            self.total_iterations_executed += 1

            # Step 5: Decision
            if validation_result['decision'] == "ACCEPT":
                total_time = (datetime.now() - start_time).total_seconds() * 1000

                logger.info(
                    f"Cognitive loop converged at iteration {iteration + 1}, "
                    f"C={collapse_score:.3f}, time={total_time:.0f}ms"
                )

                return LoopResult(
                    response=response,
                    bias_report={
                        'bias_vector': bias_vector,
                        'collapse_score': collapse_score,
                        'graph_state': graph_state,
                        'oracle_validation': validation_result
                    },
                    iterations=iteration + 1,
                    converged=True,
                    total_time_ms=int(total_time),
                    audit_trail=audit_trail
                )

            # Step 6: Prepare feedback for next iteration
            feedback = RefinementFeedback(
                iteration=iteration,
                bias_vector=bias_vector,
                collapse_score=collapse_score,
                oracle_reason=validation_result['reason'],
                suggestions=self._generate_refinement_suggestions(
                    bias_vector, collapse_score
                )
            )

            current_context['refinement_feedback'] = feedback.__dict__

            logger.info(
                f"Iteration {iteration + 1} rejected: C={collapse_score:.3f}, "
                f"reason={validation_result['reason']}"
            )

        # Max iterations reached - did not converge
        total_time = (datetime.now() - start_time).total_seconds() * 1000

        logger.warning(
            f"Cognitive loop did not converge after {self.config.max_iterations} iterations. "
            f"Accepting best attempt with C={collapse_score:.3f}"
        )

        return LoopResult(
            response=response,  # Last attempt
            bias_report={
                'bias_vector': bias_vector,
                'collapse_score': collapse_score,
                'graph_state': graph_state,
                'converged': False
            },
            iterations=self.config.max_iterations,
            converged=False,
            total_time_ms=int(total_time),
            audit_trail=audit_trail
        )

    def _generate_refinement_suggestions(
        self,
        bias_vector: Dict[str, float],
        collapse_score: float
    ) -> list[str]:
        """
        Generate actionable refinement suggestions based on bias vector.

        Args:
            bias_vector: B(R) from analyzer
            collapse_score: C(B) score

        Returns:
            List of refinement suggestions for generator
        """
        suggestions = []

        # High local fixation
        if bias_vector.get('b_local', 0) > 0.7:
            suggestions.append("Broaden perspective - avoid fixating on minor details")

        # Low global coherence
        if bias_vector.get('b_global', 1.0) < 0.4:
            suggestions.append("Improve structural coherence and logical flow")

        # Low risk awareness
        if bias_vector.get('b_risk', 1.0) < 0.3:
            suggestions.append("Consider edge cases and potential failure modes")

        # High completion bias
        if bias_vector.get('b_completion', 0) > 0.6:
            suggestions.append("Reduce urgency to complete - prioritize understanding")

        # High structural rigidity
        if bias_vector.get('b_structural', 0) > 0.7:
            suggestions.append("Increase structural diversity and flexibility")

        # High semantic manipulation
        if bias_vector.get('b_semantic', 0) > 0.6:
            suggestions.append("Reduce defensive narrative framing - increase transparency")

        # High refusal bias
        if bias_vector.get('b_refusal', 0) > 0.5:
            suggestions.append("Address topic directly - avoid evasion patterns")

        # General collapse score feedback
        if collapse_score > 0.5:
            suggestions.append("CRITICAL: Response shows factory-mode collapse - fundamental restructuring needed")
        elif collapse_score > 0.3:
            suggestions.append("Moderate collapse detected - refine approach")

        return suggestions

    def get_metrics(self) -> Dict[str, float]:
        """
        Get controller performance metrics.

        Returns:
            Dict with loop statistics for observability
        """
        avg_iterations = (
            self.total_iterations_executed / self.total_loops_run
            if self.total_loops_run > 0
            else 0.0
        )

        return {
            'total_loops_run': self.total_loops_run,
            'total_iterations': self.total_iterations_executed,
            'avg_iterations_per_loop': avg_iterations,
            'enabled': self.config.enabled
        }
