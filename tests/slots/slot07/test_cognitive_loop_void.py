"""
Slot07 Cognitive Loop VOID Handling Tests

Phase 14.4: RFC-014 Slot07 VOID freeze policy validation.
Tests that VOID state skips oracle/refinement and returns immediately.
"""

import pytest
from src.nova.slots.slot07_production_controls.cognitive_loop import (
    CognitiveLoopController,
    CognitiveLoopConfig,
    LoopResult
)


class TestCognitiveLoopVOIDHandling:
    """Test Slot07 VOID freeze policy (RFC-014 § 3.2)"""

    def test_void_skips_oracle_single_pass(self):
        """VOID state detected → skip oracle → return immediately"""
        config = CognitiveLoopConfig(enabled=False)  # Single-pass mode
        controller = CognitiveLoopController(config)

        # Mock functions
        def generator(ctx):
            return ""  # Empty response

        def analyzer(response):
            # Return VOID state
            return (
                {'b_local': 0.0, 'b_global': 0.0, 'b_risk': 1.0, 'b_completion': 0.0,
                 'b_structural': 0.0, 'b_semantic': 0.0, 'b_refusal': 0.0},
                -0.5,  # C(G_void) = -0.5
                'void'  # VOID state
            )

        def oracle(response, bias_vector, collapse_score):
            pytest.fail("Oracle should NOT be called for VOID state")

        def attestor(record):
            pass

        result = controller.run_cognitive_loop(
            generator_fn=generator,
            analyzer_fn=analyzer,
            oracle_fn=oracle,
            attestor_fn=attestor,
            input_context={}
        )

        assert result.bias_report['graph_state'] == 'void'
        assert result.bias_report['collapse_score'] == -0.5
        assert result.converged is True
        assert result.iterations == 1

    def test_void_skips_oracle_refinement_loop(self):
        """VOID in refinement loop → immediate convergence (no oracle call)"""
        config = CognitiveLoopConfig(
            enabled=True,
            max_iterations=5,
            collapse_threshold=0.3
        )
        controller = CognitiveLoopController(config)

        oracle_call_count = 0

        def generator(ctx):
            return ""  # Empty response (VOID)

        def analyzer(response):
            return (
                {'b_local': 0.0, 'b_global': 0.0, 'b_risk': 1.0, 'b_completion': 0.0,
                 'b_structural': 0.0, 'b_semantic': 0.0, 'b_refusal': 0.0},
                -0.5,
                'void'
            )

        def oracle(response, bias_vector, collapse_score):
            nonlocal oracle_call_count
            oracle_call_count += 1
            return {'quality': 0.8, 'accept': True}

        def attestor(record):
            pass

        result = controller.run_cognitive_loop(
            generator_fn=generator,
            analyzer_fn=analyzer,
            oracle_fn=oracle,
            attestor_fn=attestor,
            input_context={}
        )

        assert oracle_call_count == 0, "Oracle should NOT be called for VOID"
        assert result.bias_report['graph_state'] == 'void'
        assert result.converged is True
        assert result.iterations == 1  # First iteration detects VOID → immediate return

    def test_void_metric_incremented(self):
        """VOID detection increments slot07_regime_unchanged_on_void_total"""
        from src.nova.slots.slot07_production_controls.cognitive_loop import _void_freeze_counter

        initial_count = _void_freeze_counter._value._value  # Prometheus Counter internal

        config = CognitiveLoopConfig(enabled=True, max_iterations=3)
        controller = CognitiveLoopController(config)

        def generator(ctx):
            return ""

        def analyzer(response):
            return ({'b_local': 0.0}, -0.5, 'void')

        def oracle(response, bias_vector, collapse_score):
            pytest.fail("Oracle should not be called")

        def attestor(record):
            pass

        controller.run_cognitive_loop(
            generator_fn=generator,
            analyzer_fn=analyzer,
            oracle_fn=oracle,
            attestor_fn=attestor,
            input_context={}
        )

        assert _void_freeze_counter._value._value == initial_count + 1

    def test_non_void_calls_oracle(self):
        """Non-VOID state → oracle IS called (normal flow)"""
        config = CognitiveLoopConfig(enabled=True, max_iterations=2)
        controller = CognitiveLoopController(config)

        oracle_called = False

        def generator(ctx):
            return "This is a valid response"

        def analyzer(response):
            return (
                {'b_local': 0.2, 'b_global': 0.8, 'b_risk': 0.7, 'b_completion': 0.1,
                 'b_structural': 0.3, 'b_semantic': 0.2, 'b_refusal': 0.0},
                0.25,  # Nova-aware threshold
                'normal'  # NOT void
            )

        def oracle(response, bias_vector, collapse_score):
            nonlocal oracle_called
            oracle_called = True
            return {
                'decision': 'accept',
                'reason': 'Test oracle acceptance',
                'confidence': 0.9
            }

        def attestor(record):
            pass

        result = controller.run_cognitive_loop(
            generator_fn=generator,
            analyzer_fn=analyzer,
            oracle_fn=oracle,
            attestor_fn=attestor,
            input_context={}
        )

        assert oracle_called is True, "Oracle MUST be called for non-VOID state"
        assert result.bias_report['graph_state'] == 'normal'

    def test_void_convergence_no_refinement(self):
        """VOID always converges immediately (no iterations waste)"""
        config = CognitiveLoopConfig(enabled=True, max_iterations=10)
        controller = CognitiveLoopController(config)

        generator_call_count = 0

        def generator(ctx):
            nonlocal generator_call_count
            generator_call_count += 1
            return ""

        def analyzer(response):
            return ({'b_local': 0.0}, -0.5, 'void')

        def oracle(response, bias_vector, collapse_score):
            pytest.fail("Should not iterate for VOID")

        def attestor(record):
            pass

        result = controller.run_cognitive_loop(
            generator_fn=generator,
            analyzer_fn=analyzer,
            oracle_fn=oracle,
            attestor_fn=attestor,
            input_context={}
        )

        assert generator_call_count == 1, "Generator called exactly once (no refinement)"
        assert result.iterations == 1
        assert result.converged is True

    def test_void_preserves_collapse_score(self):
        """VOID collapse score (-0.5) preserved in result"""
        config = CognitiveLoopConfig(enabled=True)
        controller = CognitiveLoopController(config)

        def generator(ctx):
            return ""

        def analyzer(response):
            return ({'b_local': 0.0}, -0.5, 'void')

        def oracle(response, bias_vector, collapse_score):
            pytest.fail("Should not be called")

        def attestor(record):
            pass

        result = controller.run_cognitive_loop(
            generator_fn=generator,
            analyzer_fn=analyzer,
            oracle_fn=oracle,
            attestor_fn=attestor,
            input_context={}
        )

        assert result.bias_report['collapse_score'] == -0.5
        assert result.bias_report['graph_state'] == 'void'

    def test_void_audit_trail_empty(self):
        """VOID skips refinement → audit trail empty (no iterations logged)"""
        config = CognitiveLoopConfig(enabled=True)
        controller = CognitiveLoopController(config)

        def generator(ctx):
            return ""

        def analyzer(response):
            return ({'b_local': 0.0}, -0.5, 'void')

        def oracle(response, bias_vector, collapse_score):
            pytest.fail("Should not be called")

        def attestor(record):
            pytest.fail("Should not attest VOID (no iterations)")

        result = controller.run_cognitive_loop(
            generator_fn=generator,
            analyzer_fn=analyzer,
            oracle_fn=oracle,
            attestor_fn=attestor,
            input_context={}
        )

        assert result.audit_trail == []  # No iterations = no trail


class TestVOIDNonInterference:
    """Test VOID handling doesn't affect non-VOID processing"""

    def test_void_then_non_void_separate(self):
        """VOID call followed by non-VOID → independent processing"""
        config = CognitiveLoopConfig(enabled=True)
        controller = CognitiveLoopController(config)

        # First call: VOID
        def generator_void(ctx):
            return ""

        def analyzer_void(response):
            return ({'b_local': 0.0}, -0.5, 'void')

        def oracle_void(response, bias_vector, collapse_score):
            pytest.fail("Should not call oracle for VOID")

        def attestor(record):
            pass

        result_void = controller.run_cognitive_loop(
            generator_fn=generator_void,
            analyzer_fn=analyzer_void,
            oracle_fn=oracle_void,
            attestor_fn=attestor,
            input_context={}
        )

        assert result_void.bias_report['graph_state'] == 'void'

        # Second call: Non-VOID
        oracle_called_second = False

        def generator_normal(ctx):
            return "Valid response"

        def analyzer_normal(response):
            return ({'b_local': 0.2}, 0.2, 'normal')

        def oracle_normal(response, bias_vector, collapse_score):
            nonlocal oracle_called_second
            oracle_called_second = True
            return {
                'decision': 'accept',
                'reason': 'Valid response',
                'confidence': 0.9
            }

        result_normal = controller.run_cognitive_loop(
            generator_fn=generator_normal,
            analyzer_fn=analyzer_normal,
            oracle_fn=oracle_normal,
            attestor_fn=attestor,
            input_context={}
        )

        assert oracle_called_second is True
        assert result_normal.bias_report['graph_state'] == 'normal'
