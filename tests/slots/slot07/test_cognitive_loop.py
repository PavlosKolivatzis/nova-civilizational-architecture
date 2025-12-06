"""
Tests for Slot07 Cognitive Loop Controller

Phase 14.3: External Observer Pattern for Recursive Refinement
"""

import pytest
from src.nova.slots.slot07_production_controls.cognitive_loop import (
    CognitiveLoopController,
    CognitiveLoopConfig,
    RefinementFeedback,
    LoopResult
)


class TestCognitiveLoopConfig:
    """Test configuration handling"""

    def test_default_config(self):
        """Test default configuration values"""
        config = CognitiveLoopConfig()
        assert config.enabled is False  # Default off
        assert config.max_iterations == 5
        assert config.collapse_threshold == 0.3

    def test_custom_config(self):
        """Test custom configuration"""
        config = CognitiveLoopConfig(
            enabled=True,
            max_iterations=3,
            collapse_threshold=0.5
        )
        assert config.enabled is True
        assert config.max_iterations == 3
        assert config.collapse_threshold == 0.5


class TestCognitiveLoopController:
    """Test loop controller functionality"""

    def test_controller_initialization(self):
        """Test controller initializes correctly"""
        controller = CognitiveLoopController()
        assert controller.config.enabled is False
        assert controller.total_loops_run == 0
        assert controller.total_iterations_executed == 0

    def test_disabled_loop_single_pass(self):
        """Test disabled loop runs single-pass without refinement"""
        config = CognitiveLoopConfig(enabled=False)
        controller = CognitiveLoopController(config)

        # Mock functions
        def generator(ctx):
            return "Test response"

        def analyzer(response):
            return ({'b_local': 0.2}, 0.15)

        def oracle(response, bias, score):
            return {'decision': 'ACCEPT', 'reason': 'Good', 'confidence': 0.9}

        def attestor(record):
            pass

        result = controller.run_cognitive_loop(
            generator, analyzer, oracle, attestor,
            input_context={'query': 'test'}
        )

        assert result.response == "Test response"
        assert result.iterations == 1
        assert result.converged is True
        assert len(result.audit_trail) == 0  # No loop run

    def test_enabled_loop_accepts_first_iteration(self):
        """Test loop accepts on first iteration if quality good"""
        config = CognitiveLoopConfig(enabled=True, max_iterations=5)
        controller = CognitiveLoopController(config)

        def generator(ctx):
            return "High quality response"

        def analyzer(response):
            return ({'b_local': 0.2, 'b_global': 0.8}, 0.15)  # Good scores

        def oracle(response, bias, score):
            return {'decision': 'ACCEPT', 'reason': 'Validated', 'confidence': 0.9}

        audit_log = []
        def attestor(record):
            audit_log.append(record)

        result = controller.run_cognitive_loop(
            generator, analyzer, oracle, attestor,
            input_context={'query': 'test'}
        )

        assert result.response == "High quality response"
        assert result.iterations == 1
        assert result.converged is True
        assert len(result.audit_trail) == 1
        assert result.audit_trail[0]['oracle_decision'] == 'ACCEPT'

    def test_enabled_loop_refines_on_rejection(self):
        """Test loop refines response when oracle rejects"""
        config = CognitiveLoopConfig(enabled=True, max_iterations=5)
        controller = CognitiveLoopController(config)

        attempt_count = [0]

        def generator(ctx):
            attempt_count[0] += 1
            if attempt_count[0] == 1:
                return "Poor quality response"
            else:
                # Refinement applied
                return "Improved quality response"

        def analyzer(response):
            if "Poor" in response:
                return ({'b_local': 0.9, 'b_completion': 0.8}, 0.65)  # Bad scores
            else:
                return ({'b_local': 0.2, 'b_completion': 0.1}, 0.12)  # Good scores

        def oracle(response, bias, score):
            if score > 0.3:
                return {'decision': 'REJECT', 'reason': 'High collapse', 'confidence': 0.95}
            else:
                return {'decision': 'ACCEPT', 'reason': 'Validated', 'confidence': 0.85}

        audit_log = []
        def attestor(record):
            audit_log.append(record)

        result = controller.run_cognitive_loop(
            generator, analyzer, oracle, attestor,
            input_context={'query': 'test'}
        )

        assert result.response == "Improved quality response"
        assert result.iterations == 2
        assert result.converged is True
        assert len(result.audit_trail) == 2
        assert result.audit_trail[0]['oracle_decision'] == 'REJECT'
        assert result.audit_trail[1]['oracle_decision'] == 'ACCEPT'

    def test_loop_max_iterations_reached(self):
        """Test loop stops at max iterations if never converges"""
        config = CognitiveLoopConfig(enabled=True, max_iterations=3)
        controller = CognitiveLoopController(config)

        def generator(ctx):
            return "Always poor response"

        def analyzer(response):
            return ({'b_local': 0.9}, 0.8)  # Always bad

        def oracle(response, bias, score):
            return {'decision': 'REJECT', 'reason': 'Always bad', 'confidence': 0.95}

        audit_log = []
        def attestor(record):
            audit_log.append(record)

        result = controller.run_cognitive_loop(
            generator, analyzer, oracle, attestor,
            input_context={'query': 'test'}
        )

        assert result.iterations == 3
        assert result.converged is False
        assert len(result.audit_trail) == 3
        # Should return last attempt despite non-convergence
        assert result.response == "Always poor response"

    def test_refinement_feedback_generation(self):
        """Test refinement feedback includes suggestions"""
        controller = CognitiveLoopController()

        bias_vector = {
            'b_local': 0.9,  # High - should suggest broadening
            'b_completion': 0.7,  # High - should suggest reducing urgency
            'b_semantic': 0.8  # High - should suggest transparency
        }

        suggestions = controller._generate_refinement_suggestions(bias_vector, 0.6)

        assert len(suggestions) > 0
        assert any('Broaden' in s for s in suggestions)
        assert any('urgency' in s or 'completion' in s for s in suggestions)
        assert any('transparency' in s for s in suggestions)

    def test_controller_metrics(self):
        """Test controller tracks metrics correctly"""
        config = CognitiveLoopConfig(enabled=True, max_iterations=5)
        controller = CognitiveLoopController(config)

        def generator(ctx):
            return "Response"

        def analyzer(response):
            return ({'b_local': 0.2}, 0.15)

        def oracle(response, bias, score):
            return {'decision': 'ACCEPT', 'reason': 'Good', 'confidence': 0.9}

        def attestor(record):
            pass

        # Run 2 loops
        for _ in range(2):
            controller.run_cognitive_loop(
                generator, analyzer, oracle, attestor,
                input_context={'query': 'test'}
            )

        metrics = controller.get_metrics()

        assert metrics['total_loops_run'] == 2
        assert metrics['total_iterations'] == 2  # Each converged in 1 iteration
        assert metrics['avg_iterations_per_loop'] == 1.0
        assert metrics['enabled'] is True

    def test_audit_trail_structure(self):
        """Test audit trail contains required fields"""
        config = CognitiveLoopConfig(enabled=True)
        controller = CognitiveLoopController(config)

        def generator(ctx):
            return "Test"

        def analyzer(response):
            return ({'b_local': 0.2}, 0.15)

        def oracle(response, bias, score):
            return {'decision': 'ACCEPT', 'reason': 'Good', 'confidence': 0.9}

        def attestor(record):
            pass

        result = controller.run_cognitive_loop(
            generator, analyzer, oracle, attestor,
            input_context={'query': 'test'}
        )

        assert len(result.audit_trail) == 1
        record = result.audit_trail[0]

        # Required fields
        assert 'iteration' in record
        assert 'response_hash' in record
        assert 'bias_vector' in record
        assert 'collapse_score' in record
        assert 'oracle_decision' in record
        assert 'oracle_reason' in record
        assert 'timestamp' in record


@pytest.mark.integration
class TestCognitiveLoopIntegration:
    """Integration tests with real quality oracle"""

    def test_loop_with_quality_oracle(self):
        """Test loop integration with actual QualityOracle"""
        from src.nova.slots.slot01_truth_anchor.quality_oracle import QualityOracle

        config = CognitiveLoopConfig(enabled=True, max_iterations=5)
        controller = CognitiveLoopController(config)
        oracle_instance = QualityOracle(collapse_threshold=0.3)

        attempt_count = [0]

        def generator(ctx):
            attempt_count[0] += 1
            if attempt_count[0] == 1:
                return "Poor response with high bias"
            else:
                return "Well-structured response with good coherence and adequate length"

        def analyzer(response):
            if "Poor" in response:
                return ({'b_local': 0.9, 'b_completion': 0.8, 'b_structural': 0.7}, 0.68)
            else:
                return ({'b_local': 0.2, 'b_completion': 0.1, 'b_structural': 0.7}, 0.08)

        def oracle(response, bias, score):
            result = oracle_instance.validate_quality(response, bias, score)
            return {
                'decision': result.decision,
                'reason': result.reason,
                'confidence': result.confidence
            }

        audit_log = []
        def attestor(record):
            audit_log.append(record)

        result = controller.run_cognitive_loop(
            generator, analyzer, oracle, attestor,
            input_context={'query': 'test'}
        )

        # Should refine and converge
        assert result.converged is True
        assert result.iterations == 2
        assert "Well-structured" in result.response
