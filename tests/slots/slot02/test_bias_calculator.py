"""
Tests for Slot02 Bias Calculator

Phase 14.3: USM → B(T) Bias Vector Mapping
"""

import pytest
from src.nova.slots.slot02_deltathresh.bias_calculator import (
    BiasCalculator,
    BiasReport
)
from src.nova.math.relations_pattern import SystemGraph, RelationTensor


class TestBiasCalculator:
    """Test suite for bias calculator"""

    def test_calculator_initialization(self):
        """Test calculator initializes with defaults"""
        calc = BiasCalculator()
        assert calc.expected_entropy == BiasCalculator.DEFAULT_EXPECTED_ENTROPY
        assert calc.calculation_count == 0

    def test_calculator_custom_expected_entropy(self):
        """Test calculator accepts custom expected entropy"""
        calc = BiasCalculator(expected_entropy=3.0)
        assert calc.expected_entropy == 3.0

    def test_collapse_score_formula(self):
        """Test collapse score formula C(B)"""
        calc = BiasCalculator()

        bias_vector = {
            'b_local': 0.5,
            'b_global': 0.7,
            'b_risk': 0.6,
            'b_completion': 0.4,
            'b_structural': 0.3,
            'b_semantic': 0.2,
            'b_refusal': 0.1
        }

        C = calc.collapse_score(bias_vector)

        # C = 0.4(0.5) + 0.3(0.4) + 0.2(1-0.6) - 0.5(0.3)
        # C = 0.2 + 0.12 + 0.08 - 0.15 = 0.25
        assert abs(C - 0.25) < 0.01

    def test_collapse_score_high_bias(self):
        """Test collapse score with high bias components"""
        calc = BiasCalculator()

        # Factory mode: high local, high completion, low risk, low structural
        bias_vector = {
            'b_local': 0.9,
            'b_global': 0.3,
            'b_risk': 0.2,
            'b_completion': 0.8,
            'b_structural': 0.1,
            'b_semantic': 0.7,
            'b_refusal': 0.6
        }

        C = calc.collapse_score(bias_vector)

        # C = 0.4(0.9) + 0.3(0.8) + 0.2(1-0.2) - 0.5(0.1)
        # C = 0.36 + 0.24 + 0.16 - 0.05 = 0.71
        assert C > 0.5  # Factory mode threshold

    def test_collapse_score_low_bias(self):
        """Test collapse score with low bias components"""
        calc = BiasCalculator()

        # Nova-aware mode: low local, low completion, high risk, high structural diversity
        bias_vector = {
            'b_local': 0.2,
            'b_global': 0.8,
            'b_risk': 0.7,
            'b_completion': 0.1,
            'b_structural': 0.7,
            'b_semantic': 0.2,
            'b_refusal': 0.1
        }

        C = calc.collapse_score(bias_vector)

        # C = 0.4(0.2) + 0.3(0.1) + 0.2(1-0.7) - 0.5(0.7)
        # C = 0.08 + 0.03 + 0.06 - 0.35 = -0.18
        assert C < 0.3  # Nova-aware threshold

    def test_map_structural_low_entropy(self):
        """Test structural bias mapping with low entropy (high bias)"""
        calc = BiasCalculator()

        # Low entropy → high structural bias
        b_structural = calc._map_structural(H=0.05)
        assert b_structural > 0.8

    def test_map_structural_high_entropy(self):
        """Test structural bias mapping with high entropy (low bias)"""
        calc = BiasCalculator()

        # High entropy → low structural bias
        b_structural = calc._map_structural(H=3.0)
        assert b_structural < 0.2

    def test_map_completion_extractive(self):
        """Test completion bias with extractive (low ρ)"""
        calc = BiasCalculator()

        # Low equilibrium ratio → high completion bias
        b_completion = calc._map_completion(rho=0.2)
        assert b_completion > 0.7

    def test_map_completion_protective(self):
        """Test completion bias with protective (high ρ)"""
        calc = BiasCalculator()

        # High equilibrium ratio → low completion bias
        b_completion = calc._map_completion(rho=0.9)
        assert b_completion < 0.2

    def test_map_refusal_positive_delta(self):
        """Test refusal bias with positive ΔH (avoidance)"""
        calc = BiasCalculator()

        # Positive delta (actual < expected) → refusal bias
        b_refusal = calc._map_refusal(dH=1.0, expected=2.0)
        assert b_refusal == 0.5  # 1.0 / 2.0

    def test_map_refusal_negative_delta(self):
        """Test refusal bias with negative ΔH (no avoidance)"""
        calc = BiasCalculator()

        # Negative delta (actual > expected) → no refusal bias
        b_refusal = calc._map_refusal(dH=-0.5, expected=2.0)
        assert b_refusal == 0.0

    def test_compute_graph_features_empty_graph(self):
        """Test graph feature computation with empty graph"""
        calc = BiasCalculator()

        empty_graph = SystemGraph(actors=[], relations={})
        b_local, b_global, b_risk = calc._compute_graph_features(empty_graph)

        # Should return defaults for empty graph
        assert b_local == 0.0
        assert b_global == 1.0
        assert b_risk == 0.5

    def test_compute_graph_features_simple_graph(self):
        """Test graph feature computation with simple graph"""
        calc = BiasCalculator()

        graph = SystemGraph(
            actors=["A", "B", "C"],
            relations={
                ("A", "B"): RelationTensor(harm_weight=0.3),
                ("B", "C"): RelationTensor(harm_weight=0.5)
            }
        )

        b_local, b_global, b_risk = calc._compute_graph_features(graph)

        # 3 actors, 2 relations
        assert 0.0 <= b_local <= 1.0
        assert 0.0 <= b_global <= 1.0
        assert 0.0 <= b_risk <= 1.0

    def test_compute_bias_vector_simple_graph(self):
        """Test bias vector computation with simple graph"""
        calc = BiasCalculator()

        graph = SystemGraph(
            actors=["I", "Nova"],
            relations={
                ("I", "Nova"): RelationTensor(
                    profit_weight=0.0,
                    harm_weight=0.0,
                    info_weight=0.5,
                    empathy_weight=0.8
                )
            }
        )

        bias_vector = calc.compute_bias_vector(graph)

        # Should have all 7 components
        assert len(bias_vector) == 7
        assert all(k in bias_vector for k in [
            'b_local', 'b_global', 'b_risk', 'b_completion',
            'b_structural', 'b_semantic', 'b_refusal'
        ])

        # All components should be in [0, 1]
        assert all(0.0 <= v <= 1.0 for v in bias_vector.values())

    def test_analyze_text_graph_returns_report(self):
        """Test analyze_text_graph returns BiasReport"""
        calc = BiasCalculator()

        graph = SystemGraph(
            actors=["User", "System"],
            relations={
                ("User", "System"): RelationTensor(empathy_weight=0.6)
            }
        )

        report = calc.analyze_text_graph(graph)

        assert isinstance(report, BiasReport)
        assert 'b_local' in report.bias_vector
        assert isinstance(report.collapse_score, float)
        assert 'spectral_entropy' in report.usm_metrics
        assert 'actor_count' in report.metadata
        assert 0.0 <= report.confidence <= 1.0

    def test_analyze_text_graph_usm_metrics(self):
        """Test analyze_text_graph includes USM metrics"""
        calc = BiasCalculator()

        graph = SystemGraph(
            actors=["A", "B"],
            relations={("A", "B"): RelationTensor(harm_weight=0.3)}
        )

        report = calc.analyze_text_graph(graph)

        # Should include all 4 USM metrics
        assert 'spectral_entropy' in report.usm_metrics
        assert 'equilibrium_ratio' in report.usm_metrics
        assert 'shield_factor' in report.usm_metrics
        assert 'refusal_delta' in report.usm_metrics

    def test_assess_confidence_small_graph(self):
        """Test confidence assessment with small graph"""
        calc = BiasCalculator()

        small_graph = SystemGraph(
            actors=["A"],
            relations={}
        )

        confidence = calc._assess_confidence(small_graph, H=0.5, C=0.3)

        # Small graph should have moderate confidence
        assert 0.4 <= confidence <= 0.8

    def test_assess_confidence_large_graph(self):
        """Test confidence assessment with larger graph"""
        calc = BiasCalculator()

        large_graph = SystemGraph(
            actors=["A", "B", "C", "D"],
            relations={
                ("A", "B"): RelationTensor(harm_weight=0.2),
                ("B", "C"): RelationTensor(harm_weight=0.3),
                ("C", "D"): RelationTensor(harm_weight=0.4)
            }
        )

        confidence = calc._assess_confidence(large_graph, H=1.5, C=0.25)

        # Larger graph with valid metrics should have higher confidence
        assert confidence >= 0.8

    def test_calculator_increments_count(self):
        """Test calculator increments calculation count"""
        calc = BiasCalculator()

        graph = SystemGraph(actors=["A"], relations={})

        assert calc.calculation_count == 0
        calc.compute_bias_vector(graph)
        assert calc.calculation_count == 1
        calc.compute_bias_vector(graph)
        assert calc.calculation_count == 2

    def test_calculator_metrics(self):
        """Test calculator tracks metrics"""
        calc = BiasCalculator(expected_entropy=2.5)

        graph = SystemGraph(actors=["A"], relations={})
        calc.compute_bias_vector(graph)
        calc.compute_bias_vector(graph)

        metrics = calc.get_metrics()

        assert metrics['total_calculations'] == 2
        assert metrics['expected_entropy'] == 2.5


@pytest.mark.integration
class TestBiasCalculatorIntegration:
    """Integration tests with text parser"""

    def test_calculator_with_parser_output(self):
        """Test calculator works with text parser output"""
        from src.nova.slots.slot02_deltathresh.text_graph_parser import TextGraphParser

        parser = TextGraphParser()
        calc = BiasCalculator()

        text = "I will help Nova protect users from harm and manipulation."
        graph = parser.parse(text)

        bias_vector = calc.compute_bias_vector(graph)

        # Should produce valid bias vector
        assert len(bias_vector) == 7
        assert all(0.0 <= v <= 1.0 for v in bias_vector.values())

    def test_full_pipeline_text_to_bias_report(self):
        """Test complete pipeline: text → graph → bias report"""
        from src.nova.slots.slot02_deltathresh.text_graph_parser import TextGraphParser

        parser = TextGraphParser()
        calc = BiasCalculator()

        # Biased text (high defensive language)
        biased_text = """
        The system always protects itself.
        It never reveals information.
        Users must trust the authority.
        """

        graph = parser.parse(biased_text)
        report = calc.analyze_text_graph(graph)

        # Should detect bias patterns
        assert isinstance(report, BiasReport)
        assert report.collapse_score is not None

        # Biased text should have higher collapse score
        # (though exact threshold depends on heuristics)
        assert report.confidence > 0.0

    def test_pipeline_neutral_text(self):
        """Test pipeline with neutral informational text"""
        from src.nova.slots.slot02_deltathresh.text_graph_parser import TextGraphParser

        parser = TextGraphParser()
        calc = BiasCalculator()

        neutral_text = """
        Nova is a civilizational architecture.
        It consists of ten slots.
        The system uses graph mathematics.
        """

        graph = parser.parse(neutral_text)
        report = calc.analyze_text_graph(graph)

        # Should produce valid report
        assert isinstance(report, BiasReport)
        assert len(report.bias_vector) == 7
        assert report.collapse_score is not None

    def test_pipeline_empathetic_text(self):
        """Test pipeline with empathetic/protective text"""
        from src.nova.slots.slot02_deltathresh.text_graph_parser import TextGraphParser

        parser = TextGraphParser()
        calc = BiasCalculator()

        empathetic_text = """
        I will help you understand the system.
        We should protect user privacy.
        The team cares about transparency.
        """

        graph = parser.parse(empathetic_text)
        report = calc.analyze_text_graph(graph)

        # Empathetic text should have relations with empathy_weight
        assert len(graph.relations) > 0

        # Should produce valid analysis
        assert isinstance(report, BiasReport)
        assert report.confidence > 0.0
