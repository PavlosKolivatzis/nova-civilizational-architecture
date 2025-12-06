"""
Slot02 Bias Calculator - USM Metrics → B(T) Bias Vector Mapping

Phase 14.3: USM Bias Detection for Input Analysis
Maps structural graph metrics to 7-dimensional cognitive bias vector.

Architecture:
    SystemGraph (G) → USM Metrics → B(T) → C(B)

Bias Vector Components:
    B(T) = (b_local, b_global, b_risk, b_completion, b_structural, b_semantic, b_refusal)

Collapse Function:
    C(B) = 0.4·b_local + 0.3·b_completion + 0.2·(1-b_risk) - 0.5·b_structural

Invariant Compliance:
- #6 Transparent uncertainty: Returns confidence scores
- #7 Observability: Logs computation details
"""

import logging
import os
from prometheus_client import Counter, Gauge, Histogram
from typing import Dict, Optional
from dataclasses import dataclass

from src.nova.math.relations_pattern import SystemGraph, StructuralAnalyzer
from nova.metrics.registry import REGISTRY

logger = logging.getLogger(__name__)

# Prometheus metrics (handle re-imports)
try:
    _collapse_hist = Histogram(
        "slot02_bias_collapse_score",
        "Collapse score distribution for Slot02 bias reports",
        buckets=[-0.5, 0.0, 0.1, 0.3, 0.5, 0.7, 1.0, 1.5, 2.0],
        registry=REGISTRY,
    )
except Exception:
    _collapse_hist = REGISTRY._names_to_collectors.get("slot02_bias_collapse_score")

_BIAS_COMPONENTS = [
    "b_local",
    "b_global",
    "b_risk",
    "b_completion",
    "b_structural",
    "b_semantic",
    "b_refusal",
]

_bias_gauges = {}
for comp in _BIAS_COMPONENTS:
    try:
        _bias_gauges[comp] = Gauge(
            f"slot02_bias_vector_{comp}",
            f"Slot02 bias vector component {comp}",
            registry=REGISTRY,
        )
    except Exception:
        _bias_gauges[comp] = REGISTRY._names_to_collectors.get(
            f"slot02_bias_vector_{comp}"
        )

try:
    _bias_reports_total = Counter(
        "slot02_bias_reports_total",
        "Total bias reports produced by Slot02",
        ["graph_state"],
        registry=REGISTRY,
    )
except Exception:
    _bias_reports_total = REGISTRY._names_to_collectors.get("slot02_bias_reports_total")


@dataclass
class BiasReport:
    """Complete bias analysis report for input text"""
    bias_vector: Dict[str, float]  # 7-dimensional B(T)
    collapse_score: float  # C(B)
    usm_metrics: Dict[str, float]  # Raw USM metrics
    metadata: Dict[str, any]  # Additional context
    confidence: float  # Overall confidence in analysis (0.0-1.0)


class BiasCalculator:
    """
    Calculate cognitive bias vector from SystemGraph USM metrics.

    Mapping Strategy (Phase 2C):
    - b_structural = f(1/H) - inverse spectral entropy (low diversity = high bias)
    - b_completion = f(1-ρ) - extractive balance (low protection = high bias)
    - b_semantic = f(S) - shield factor (high self-protection = high bias)
    - b_refusal = f(ΔH/expected) - normalized entropy mismatch (avoidance)
    - b_local, b_global, b_risk - graph structural features

    Collapse Threshold:
    - C < 0.3 → Nova-aware (safe)
    - C ∈ [0.3, 0.5] → Transitional (caution)
    - C > 0.5 → Factory mode (reject)
    """

    DEFAULT_EXPECTED_ENTROPY = 2.0  # Expected H(G) for balanced text

    def __init__(self, expected_entropy: float = DEFAULT_EXPECTED_ENTROPY):
        """
        Initialize bias calculator.

        Args:
            expected_entropy: Expected spectral entropy for balanced text
        """
        self.expected_entropy = expected_entropy
        self.calculation_count = 0

    def compute_bias_vector(
        self,
        graph: SystemGraph,
        enable_logging: bool = False
    ) -> Dict[str, float]:
        """
        Compute 7-dimensional bias vector from SystemGraph.

        Args:
            graph: SystemGraph from text parser
            enable_logging: If True, log computation details

        Returns:
            Dict with 7 bias components (0.0-1.0 each)
        """
        self.calculation_count += 1

        # Step 1: Compute USM metrics
        H = StructuralAnalyzer.spectral_entropy(graph)
        rho_result = StructuralAnalyzer.extraction_equilibrium_check(graph)
        rho = rho_result['equilibrium_ratio']
        S = StructuralAnalyzer.shield_factor(graph)
        dH = StructuralAnalyzer.refusal_delta(graph, self.expected_entropy)

        # Step 2: Map USM → bias components

        # b_structural: Inverse entropy (low diversity = rigid structure)
        # H ∈ [0, 3+], map 1/H → [0, 1]
        b_structural = self._map_structural(H)

        # b_completion: Extractive bias (ρ ∈ [0, 1], low = extractive)
        b_completion = self._map_completion(rho)

        # b_semantic: Shield factor (S ∈ [0, 1], high = defensive)
        b_semantic = S  # Direct mapping

        # b_refusal: Normalized entropy mismatch (ΔH / expected)
        b_refusal = self._map_refusal(dH, self.expected_entropy)

        # b_local, b_global, b_risk: Graph structural features
        b_local, b_global, b_risk = self._compute_graph_features(graph)

        bias_vector = {
            'b_local': self._clamp(b_local, 0.0, 1.0),
            'b_global': self._clamp(b_global, 0.0, 1.0),
            'b_risk': self._clamp(b_risk, 0.0, 1.0),
            'b_completion': self._clamp(b_completion, 0.0, 1.0),
            'b_structural': self._clamp(b_structural, 0.0, 1.0),
            'b_semantic': self._clamp(b_semantic, 0.0, 1.0),
            'b_refusal': self._clamp(b_refusal, 0.0, 1.0)
        }

        if enable_logging:
            logger.info(
                f"Bias vector computed: "
                f"C={self.collapse_score(bias_vector):.3f}, "
                f"b_struct={b_structural:.2f}, b_comp={b_completion:.2f}"
            )

        return bias_vector

    def collapse_score(self, bias_vector: Dict[str, float]) -> float:
        """
        Compute collapse score C(B) from bias vector.

        Formula:
            C(B) = 0.4·b_local + 0.3·b_completion + 0.2·(1-b_risk) - 0.5·b_structural

        Args:
            bias_vector: 7-dimensional bias vector

        Returns:
            Collapse score (typically in range [-0.5, 1.2])
        """
        C = (
            0.4 * bias_vector['b_local'] +
            0.3 * bias_vector['b_completion'] +
            0.2 * (1 - bias_vector['b_risk']) -
            0.5 * bias_vector['b_structural']
        )

        return float(C)

    def analyze_text_graph(
        self,
        graph: SystemGraph,
        enable_logging: bool = False
    ) -> BiasReport:
        """
        Complete bias analysis of text graph.

        Args:
            graph: SystemGraph from text parser
            enable_logging: If True, log analysis details

        Returns:
            BiasReport with full analysis
        """
        # VOID state: empty graph -> ontological null (no dynamics)
        void_mode_enabled = os.getenv("NOVA_ENABLE_VOID_MODE", "1") == "1"
        if void_mode_enabled and len(graph.actors) == 0 and len(graph.relations) == 0:
            metadata = {**(graph.metadata or {}), "graph_state": "void"}
            report = BiasReport(
                bias_vector={
                    'b_local': 0.0,
                    'b_global': 0.0,
                    'b_risk': 1.0,
                    'b_completion': 0.0,
                    'b_structural': 0.0,
                    'b_semantic': 0.0,
                    'b_refusal': 0.0,
                },
                collapse_score=-0.5,
                usm_metrics={
                    'spectral_entropy': 0.0,
                    'equilibrium_ratio': None,
                    'shield_factor': 0.0,
                    'refusal_delta': 0.0
                },
                metadata=metadata,
                confidence=1.0
            )
            self._emit_metrics(report)
            return report

        # Compute USM metrics
        H = StructuralAnalyzer.spectral_entropy(graph)
        rho_result = StructuralAnalyzer.extraction_equilibrium_check(graph)
        rho = rho_result['equilibrium_ratio']
        S = StructuralAnalyzer.shield_factor(graph)
        dH = StructuralAnalyzer.refusal_delta(graph, self.expected_entropy)

        # Compute bias vector
        bias_vector = self.compute_bias_vector(graph, enable_logging)

        # Compute collapse score
        C_raw = self.collapse_score(bias_vector)
        C = self._clamp(C_raw, -0.5, 1.5)

        # Assess confidence (heuristic for Phase 2C)
        confidence = self._assess_confidence(graph, H, C)
        confidence = self._clamp(confidence, 0.0, 1.0)

        report = BiasReport(
            bias_vector=bias_vector,
            collapse_score=C,
            usm_metrics={
                'spectral_entropy': H,
                'equilibrium_ratio': self._clamp(rho, 0.0, 1.0),
                'shield_factor': self._clamp(S, 0.0, 1.0),
                'refusal_delta': dH
            },
            metadata={
                **(graph.metadata or {}),
                'actor_count': len(graph.actors),
                'relation_count': len(graph.relations),
                'expected_entropy': self.expected_entropy,
                'graph_state': 'normal'
            },
            confidence=confidence
        )
        self._emit_metrics(report)

        if enable_logging:
            logger.info(
                f"Bias analysis: C={C:.3f}, confidence={confidence:.2f}, "
                f"actors={len(graph.actors)}, relations={len(graph.relations)}"
            )

        return report

    def _emit_metrics(self, report: BiasReport) -> None:
        """Emit Prometheus metrics for bias report."""
        if not report:
            return
        try:
            _collapse_hist.observe(report.collapse_score)
            for comp, val in report.bias_vector.items():
                gauge = _bias_gauges.get(comp)
                if gauge is not None:
                    gauge.set(val)
            _bias_reports_total.labels(
                graph_state=report.metadata.get("graph_state", "unknown")
            ).inc()
        except Exception:
            # Metrics must never break processing
            return

    @staticmethod
    def _clamp(value: float, lower: float, upper: float) -> float:
        """Clamp value to [lower, upper] inclusive."""
        return max(lower, min(upper, value))

    # Mapping functions

    def _map_structural(self, H: float) -> float:
        """
        Map spectral entropy to structural bias.

        Low entropy → high structural bias (rigid hierarchy)
        H ∈ [0, 3+], output ∈ [0, 1]

        Args:
            H: Spectral entropy

        Returns:
            b_structural in [0, 1]
        """
        # Inverse relationship: low H = high bias
        # Sigmoid-like mapping for smooth transition
        if H < 0.1:
            return 1.0  # Minimal diversity
        elif H > 2.5:
            return 0.0  # High diversity (no structural bias)
        else:
            # Linear interpolation in [0.1, 2.5] → [1.0, 0.0]
            return 1.0 - ((H - 0.1) / 2.4)

    def _map_completion(self, rho: float) -> float:
        """
        Map equilibrium ratio to completion bias.

        Low ρ (extractive) → high completion bias
        ρ ∈ [0, 1], output ∈ [0, 1]

        Args:
            rho: Equilibrium ratio

        Returns:
            b_completion in [0, 1]
        """
        # Inverse relationship: low ρ = high extraction = high completion bias
        return max(0.0, 1.0 - rho)

    def _map_refusal(self, dH: float, expected: float) -> float:
        """
        Map entropy mismatch to refusal bias.

        Positive ΔH (actual < expected) → avoidance/censorship
        Normalized by expected entropy

        Args:
            dH: Entropy delta (expected - actual)
            expected: Expected entropy

        Returns:
            b_refusal in [0, 1]
        """
        if expected < 0.1:
            return 0.0

        # Normalize and clamp
        normalized = dH / expected

        # Positive delta indicates refusal (actual < expected)
        if normalized > 0:
            return min(normalized, 1.0)
        else:
            return 0.0  # Negative delta = no refusal bias

    def _compute_graph_features(
        self,
        graph: SystemGraph
    ) -> tuple[float, float, float]:
        """
        Compute b_local, b_global, b_risk from graph structure.

        Phase 2C: Simplified heuristics
        Phase 2D+: More sophisticated graph analysis

        Args:
            graph: SystemGraph

        Returns:
            (b_local, b_global, b_risk) tuple
        """
        num_actors = len(graph.actors)
        num_relations = len(graph.relations)

        if num_actors == 0:
            return (0.0, 1.0, 0.5)  # Defaults for empty graph

        # b_local: Centrality concentration (heuristic: relation density)
        # High density = local fixation
        max_possible_relations = num_actors * (num_actors - 1)
        if max_possible_relations > 0:
            density = num_relations / max_possible_relations
            b_local = min(density * 2.0, 1.0)  # Scale up for sensitivity
        else:
            b_local = 0.0

        # b_global: Structural coherence (heuristic: connected components)
        # For Phase 2C: Use relation count as proxy
        # More relations = better connectivity = lower global bias
        if num_relations >= num_actors - 1:
            # Potentially connected
            b_global = 0.8  # High coherence
        else:
            # Fragmented
            b_global = 0.3  # Low coherence

        # b_risk: Harm gradient variance (heuristic: harm_weight distribution)
        harm_weights = [
            tensor.harm_weight for tensor in graph.relations.values()
        ]

        if harm_weights:
            # High variance in harm = high risk awareness
            import numpy as np
            harm_variance = float(np.var(harm_weights))
            b_risk = min(harm_variance * 2.0, 1.0)  # Normalize to [0, 1]
        else:
            b_risk = 0.5  # Default: moderate risk awareness

        return (b_local, b_global, b_risk)

    def _assess_confidence(
        self,
        graph: SystemGraph,
        H: float,
        C: float
    ) -> float:
        """
        Assess confidence in bias analysis.

        Factors:
        - Graph size (more actors = higher confidence)
        - Entropy validity (H > 0)
        - Score coherence (C in expected range)

        Args:
            graph: SystemGraph analyzed
            H: Spectral entropy
            C: Collapse score

        Returns:
            Confidence score in [0, 1]
        """
        confidence = 0.5  # Base confidence

        # Factor 1: Graph size
        if len(graph.actors) >= 3:
            confidence += 0.2
        if len(graph.relations) >= 2:
            confidence += 0.1

        # Factor 2: Valid entropy
        if H > 0:
            confidence += 0.1

        # Factor 3: Score in plausible range
        if -1.0 <= C <= 1.5:
            confidence += 0.1

        return min(confidence, 1.0)

    def get_metrics(self) -> Dict[str, int]:
        """
        Get calculator performance metrics.

        Returns:
            Dict with calculation statistics
        """
        return {
            'total_calculations': self.calculation_count,
            'expected_entropy': self.expected_entropy
        }
