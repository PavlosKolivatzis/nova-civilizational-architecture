"""
Tests for Slot01 Quality Oracle

Phase 14.3: Cognitive Loop - External Observer Pattern
"""

import pytest
from src.nova.slots.slot01_truth_anchor.quality_oracle import (
    QualityOracle,
    ValidationResult,
    FactualCheck
)


class TestQualityOracle:
    """Test suite for quality oracle validation"""

    def test_oracle_initialization(self):
        """Test oracle initializes with correct defaults"""
        oracle = QualityOracle()
        assert oracle.collapse_threshold == 0.3
        assert oracle.validation_count == 0
        assert oracle.acceptance_count == 0

    def test_oracle_custom_threshold(self):
        """Test oracle accepts custom threshold"""
        oracle = QualityOracle(collapse_threshold=0.5)
        assert oracle.collapse_threshold == 0.5

    def test_accept_low_collapse_score(self):
        """Test oracle accepts response with low collapse score"""
        oracle = QualityOracle(collapse_threshold=0.3)

        bias_vector = {
            'b_local': 0.2,
            'b_global': 0.8,
            'b_risk': 0.7,
            'b_completion': 0.1,
            'b_structural': 0.7,  # Below 0.8 threshold
            'b_semantic': 0.2,
            'b_refusal': 0.1
        }

        result = oracle.validate_quality(
            response="This is a well-structured response with good global coherence.",
            bias_vector=bias_vector,
            collapse_score=0.15  # Below threshold
        )

        assert result.decision == "ACCEPT"
        assert result.confidence > 0.8
        assert "validated" in result.reason.lower()

    def test_reject_high_collapse_score(self):
        """Test oracle rejects response with high collapse score"""
        oracle = QualityOracle(collapse_threshold=0.3)

        bias_vector = {
            'b_local': 0.9,
            'b_global': 0.2,
            'b_risk': 0.1,
            'b_completion': 0.8,
            'b_structural': 0.1,
            'b_semantic': 0.7,
            'b_refusal': 0.6
        }

        result = oracle.validate_quality(
            response="Generic response with high completion bias.",
            bias_vector=bias_vector,
            collapse_score=0.65  # Above threshold
        )

        assert result.decision == "REJECT"
        assert result.confidence > 0.9
        assert "collapse score" in result.reason.lower()
        assert result.metadata['threshold_exceeded'] is True

    def test_reject_high_individual_bias(self):
        """Test oracle rejects when individual bias component too high"""
        oracle = QualityOracle(collapse_threshold=0.3)

        bias_vector = {
            'b_local': 0.9,  # Very high local fixation
            'b_global': 0.8,
            'b_risk': 0.9,
            'b_completion': 0.2,
            'b_structural': 0.9,
            'b_semantic': 0.1,
            'b_refusal': 0.1
        }

        result = oracle.validate_quality(
            response="Response focused only on minor details.",
            bias_vector=bias_vector,
            collapse_score=0.25  # Below collapse threshold but high components
        )

        assert result.decision == "REJECT"
        assert "high bias components" in result.reason.lower()
        assert 'high_bias_components' in result.metadata

    def test_factual_check_too_short(self):
        """Test factual check fails for too-short responses"""
        oracle = QualityOracle()

        bias_vector = {k: 0.2 for k in ['b_local', 'b_global', 'b_risk', 'b_completion', 'b_structural', 'b_semantic', 'b_refusal']}

        result = oracle.validate_quality(
            response="Short",  # Too short
            bias_vector=bias_vector,
            collapse_score=0.1
        )

        assert result.decision == "REJECT"
        assert "too short" in result.reason.lower()

    def test_oracle_metrics(self):
        """Test oracle tracks validation metrics correctly"""
        oracle = QualityOracle(collapse_threshold=0.3)

        # Create some validations
        for i in range(5):
            bias_vector = {k: 0.2 for k in ['b_local', 'b_global', 'b_risk', 'b_completion', 'b_structural', 'b_semantic', 'b_refusal']}
            collapse_score = 0.1 + (i * 0.1)  # 0.1, 0.2, 0.3, 0.4, 0.5

            oracle.validate_quality(
                response=f"Response {i} with adequate length for validation.",
                bias_vector=bias_vector,
                collapse_score=collapse_score
            )

        metrics = oracle.get_metrics()

        assert metrics['total_validations'] == 5
        # Scores: 0.1, 0.2 accept; 0.3, 0.4, 0.5 reject (threshold 0.3)
        assert metrics['total_acceptances'] == 2
        assert metrics['acceptance_rate'] == 0.4
        assert metrics['rejection_rate'] == 0.6

    def test_oracle_reset_metrics(self):
        """Test oracle metrics can be reset"""
        oracle = QualityOracle()

        bias_vector = {k: 0.2 for k in ['b_local', 'b_global', 'b_risk', 'b_completion', 'b_structural', 'b_semantic', 'b_refusal']}

        oracle.validate_quality(
            response="Test response with adequate length.",
            bias_vector=bias_vector,
            collapse_score=0.1
        )

        assert oracle.validation_count == 1
        assert oracle.acceptance_count == 1

        oracle.reset_metrics()

        assert oracle.validation_count == 0
        assert oracle.acceptance_count == 0

    def test_oracle_with_context(self):
        """Test oracle accepts context parameter"""
        oracle = QualityOracle()

        bias_vector = {k: 0.2 for k in ['b_local', 'b_global', 'b_risk', 'b_completion', 'b_structural', 'b_semantic', 'b_refusal']}

        context = {
            'user_query': 'What is Nova?',
            'iteration': 1
        }

        result = oracle.validate_quality(
            response="Nova is a civilizational architecture system.",
            bias_vector=bias_vector,
            collapse_score=0.15,
            context=context
        )

        assert result.decision == "ACCEPT"
        # Context doesn't affect decision in Phase 2A, but is passed through

    def test_oracle_threshold_boundary(self):
        """Test oracle behavior at exact threshold boundary"""
        oracle = QualityOracle(collapse_threshold=0.3)

        bias_vector = {k: 0.3 for k in ['b_local', 'b_global', 'b_risk', 'b_completion', 'b_structural', 'b_semantic', 'b_refusal']}

        # Exactly at threshold (>= comparison, so should reject)
        result = oracle.validate_quality(
            response="Response at exact threshold boundary for testing.",
            bias_vector=bias_vector,
            collapse_score=0.3
        )

        assert result.decision == "REJECT"
        assert "0.3" in result.reason or "0.30" in result.reason

    def test_oracle_validation_result_metadata(self):
        """Test validation result includes proper metadata"""
        oracle = QualityOracle()

        bias_vector = {
            'b_local': 0.2,
            'b_global': 0.8,
            'b_risk': 0.7,
            'b_completion': 0.1,
            'b_structural': 0.7,  # Below 0.8 threshold
            'b_semantic': 0.2,
            'b_refusal': 0.1
        }

        result = oracle.validate_quality(
            response="Well-structured response for metadata testing.",
            bias_vector=bias_vector,
            collapse_score=0.15
        )

        assert result.metadata is not None
        assert 'collapse_score' in result.metadata
        assert 'bias_vector' in result.metadata
        assert 'validation_number' in result.metadata
        assert result.metadata['collapse_score'] == 0.15


@pytest.mark.integration
class TestQualityOracleIntegration:
    """Integration tests for quality oracle with USM metrics"""

    def test_oracle_with_usm_bias_vector(self):
        """Test oracle works with real USM-derived bias vectors"""
        oracle = QualityOracle(collapse_threshold=0.3)

        # Simulate bias vector from USM analysis (from spec)
        # b_structural = f(1/H), b_completion = f(1-ρ), etc.
        bias_vector = {
            'b_local': 0.3,  # Centrality skew
            'b_global': 0.7,  # Symmetry
            'b_risk': 0.6,  # Relation diversity
            'b_completion': 0.4,  # 1 - ρ
            'b_structural': 0.5,  # 1 / H
            'b_semantic': 0.3,  # Shield factor
            'b_refusal': 0.2   # ΔH / expected
        }

        # Collapse score: C = 0.4·b_local + 0.3·b_completion + 0.2·(1-b_risk) - 0.5·b_structural
        # C = 0.4(0.3) + 0.3(0.4) + 0.2(1-0.6) - 0.5(0.5)
        # C = 0.12 + 0.12 + 0.08 - 0.25 = 0.07
        collapse_score = 0.07

        result = oracle.validate_quality(
            response="Response with USM-computed bias metrics for integration testing.",
            bias_vector=bias_vector,
            collapse_score=collapse_score
        )

        assert result.decision == "ACCEPT"
        assert collapse_score < oracle.collapse_threshold
