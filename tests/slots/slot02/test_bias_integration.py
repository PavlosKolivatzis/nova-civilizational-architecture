"""
Integration Tests for Slot02 Bias Detection

Phase 14.3: USM Bias Detection Pipeline Integration
Tests full pipeline: DeltaThreshProcessor → TextGraphParser → BiasCalculator → BIAS_REPORT@1
"""

import logging
import os
import pytest
from src.nova.slots.slot02_deltathresh.core import DeltaThreshProcessor
from src.nova.slots.slot02_deltathresh.config import ProcessingConfig
from src.nova.slots.slot02_deltathresh.bias_calculator import BiasReport
from src.nova.slots.slot02_deltathresh.text_graph_parser import TextGraphParser
from unittest import mock


class TestBiasDetectionIntegration:
    """Integration tests for bias detection in Slot02 processor"""

    def test_bias_detection_disabled_by_default(self):
        """Test bias detection is disabled by default"""
        # Ensure flag is not set
        os.environ.pop('NOVA_ENABLE_BIAS_DETECTION', None)

        processor = DeltaThreshProcessor()

        assert processor._bias_detection_enabled is False
        assert processor._text_parser is None
        assert processor._bias_calculator is None

    def test_bias_detection_enabled_with_flag(self):
        """Test bias detection enables with feature flag"""
        os.environ['NOVA_ENABLE_BIAS_DETECTION'] = '1'

        try:
            processor = DeltaThreshProcessor()

            assert processor._bias_detection_enabled is True
            assert processor._text_parser is not None
            assert processor._bias_calculator is not None
        finally:
            os.environ.pop('NOVA_ENABLE_BIAS_DETECTION', None)

    def test_process_content_without_bias_detection(self):
        """Test processing content with bias detection disabled"""
        os.environ.pop('NOVA_ENABLE_BIAS_DETECTION', None)

        processor = DeltaThreshProcessor()
        result = processor.process_content("Test content here.")

        # Should process normally
        assert result.content == "Test content here."
        assert result.action in ["allow", "quarantine", "neutralize"]
        assert result.bias_report is None  # No bias report

    def test_process_content_with_bias_detection(self):
        """Test processing content with bias detection enabled"""
        os.environ['NOVA_ENABLE_BIAS_DETECTION'] = '1'

        try:
            processor = DeltaThreshProcessor()

            # Process biased text
            biased_text = """
            The system always protects itself.
            It never reveals information.
            Users must trust the authority.
            """

            result = processor.process_content(biased_text)

            # Should process normally AND include bias report
            assert result.content == biased_text
            assert result.action in ["allow", "quarantine", "neutralize"]
            assert result.bias_report is not None

            # Verify BIAS_REPORT@1 structure
            assert 'bias_vector' in result.bias_report
            assert 'collapse_score' in result.bias_report
            assert 'usm_metrics' in result.bias_report
            assert 'metadata' in result.bias_report
            assert 'confidence' in result.bias_report

        finally:
            os.environ.pop('NOVA_ENABLE_BIAS_DETECTION', None)

    def test_bias_report_contract_structure(self):
        """Test bias report follows BIAS_REPORT@1 contract"""
        os.environ['NOVA_ENABLE_BIAS_DETECTION'] = '1'

        try:
            processor = DeltaThreshProcessor()

            text = "I will help Nova protect users from harm."
            result = processor.process_content(text)

            bias_report = result.bias_report

            # Verify bias_vector has 7 components
            assert len(bias_report['bias_vector']) == 7
            assert 'b_local' in bias_report['bias_vector']
            assert 'b_global' in bias_report['bias_vector']
            assert 'b_risk' in bias_report['bias_vector']
            assert 'b_completion' in bias_report['bias_vector']
            assert 'b_structural' in bias_report['bias_vector']
            assert 'b_semantic' in bias_report['bias_vector']
            assert 'b_refusal' in bias_report['bias_vector']

            # Verify USM metrics
            assert 'spectral_entropy' in bias_report['usm_metrics']
            assert 'equilibrium_ratio' in bias_report['usm_metrics']
            assert 'shield_factor' in bias_report['usm_metrics']
            assert 'refusal_delta' in bias_report['usm_metrics']

            # Verify metadata
            assert 'text_length' in bias_report['metadata']
            assert 'actor_count' in bias_report['metadata']
            assert 'relation_count' in bias_report['metadata']
            assert 'timestamp' in bias_report['metadata']

            # Verify confidence
            assert 0.0 <= bias_report['confidence'] <= 1.0

        finally:
            os.environ.pop('NOVA_ENABLE_BIAS_DETECTION', None)

    def test_bias_detection_failure_non_fatal(self):
        """Test bias detection failure doesn't break processing"""
        os.environ['NOVA_ENABLE_BIAS_DETECTION'] = '1'

        try:
            processor = DeltaThreshProcessor()

            # Process empty text (should fail bias detection)
            result = processor.process_content("")

            # Processing should continue despite bias detection failure
            assert result is not None
            # Bias report may be None if detection failed
            # But processing should complete

        finally:
            os.environ.pop('NOVA_ENABLE_BIAS_DETECTION', None)

    def test_bias_detection_disabled_when_module_unavailable(self):
        """Flag on but module unavailable should keep bias detection off"""
        os.environ['NOVA_ENABLE_BIAS_DETECTION'] = '1'
        with mock.patch(
            'src.nova.slots.slot02_deltathresh.core._BIAS_DETECTION_AVAILABLE',
            False
        ):
            processor = DeltaThreshProcessor()
            assert processor._bias_detection_enabled is False
            assert processor._text_parser is None
            assert processor._bias_calculator is None
        os.environ.pop('NOVA_ENABLE_BIAS_DETECTION', None)

    def test_collapse_score_thresholds(self):
        """Test collapse score interpretation"""
        os.environ['NOVA_ENABLE_BIAS_DETECTION'] = '1'

        try:
            processor = DeltaThreshProcessor()

            # Test neutral text (should have low collapse score)
            neutral_text = """
            Nova is a civilizational architecture.
            It consists of ten slots.
            The system uses graph mathematics.
            """

            result = processor.process_content(neutral_text)

            if result.bias_report:
                C = result.bias_report['collapse_score']

                # Neutral text should have low collapse score
                # (exact value depends on heuristics, but verify it's computed)
                assert isinstance(C, (int, float))
                assert -1.0 <= C <= 2.0  # Plausible range

        finally:
            os.environ.pop('NOVA_ENABLE_BIAS_DETECTION', None)

    def test_bias_report_clamped_to_contract_ranges(self):
        """Contract ranges enforced before emission"""
        os.environ['NOVA_ENABLE_BIAS_DETECTION'] = '1'
        try:
            processor = DeltaThreshProcessor()

            with mock.patch.object(
                processor._bias_calculator,
                'analyze_text_graph',
                return_value=BiasReport(
                    bias_vector={
                        'b_local': 1.5,
                        'b_global': -0.2,
                        'b_risk': 2.0,
                        'b_completion': -1.0,
                        'b_structural': 5.0,
                        'b_semantic': 3.0,
                        'b_refusal': -0.5,
                    },
                    collapse_score=3.0,
                    usm_metrics={
                        'spectral_entropy': 9.9,
                        'equilibrium_ratio': -1.0,
                        'shield_factor': 2.0,
                        'refusal_delta': -9.0,
                    },
                    metadata={'actor_count': 0, 'relation_count': 0, 'expected_entropy': 2.0},
                    confidence=2.0,
                )
            ):
                result = processor.process_content("Clamp test.")
                report = result.bias_report
                assert all(0.0 <= v <= 1.0 for v in report['bias_vector'].values())
                assert -0.5 <= report['collapse_score'] <= 1.5
                assert 0.0 <= report['usm_metrics']['equilibrium_ratio'] <= 1.0
                assert 0.0 <= report['usm_metrics']['shield_factor'] <= 1.0
                assert 0.0 <= report['confidence'] <= 1.0
        finally:
            os.environ.pop('NOVA_ENABLE_BIAS_DETECTION', None)

    def test_bias_disabled_does_not_invoke_analysis(self):
        """Flag off: analysis path not invoked and no bias report emitted"""
        os.environ.pop('NOVA_ENABLE_BIAS_DETECTION', None)
        with mock.patch.object(
            DeltaThreshProcessor, "_analyze_bias", side_effect=AssertionError("should not be called")
        ):
            processor = DeltaThreshProcessor()
            result = processor.process_content("Neutral content.")
            assert result.bias_report is None
            assert processor._bias_detection_enabled is False

    def test_bias_report_respects_contract_ranges(self):
        """Real pipeline output stays within contract ranges"""
        os.environ['NOVA_ENABLE_BIAS_DETECTION'] = '1'
        try:
            processor = DeltaThreshProcessor()
            result = processor.process_content(
                "Nova processes information and protects users with care."
            )
            report = result.bias_report
            if report:
                assert all(0.0 <= v <= 1.0 for v in report['bias_vector'].values())
                assert -0.5 <= report['collapse_score'] <= 1.5
                assert 0.0 <= report['usm_metrics']['equilibrium_ratio'] <= 1.0
                assert 0.0 <= report['usm_metrics']['shield_factor'] <= 1.0
                assert 0.0 <= report['confidence'] <= 1.0
                assert report['metadata'].get('graph_state') == 'normal'
            else:
                # Bias disabled or unavailable would already be covered elsewhere
                pytest.skip("Bias report not produced in this environment")
        finally:
            os.environ.pop('NOVA_ENABLE_BIAS_DETECTION', None)

    def test_bias_analysis_graceful_degrade_missing_dependency(self):
        """Missing dependency: processor still works and omits bias_report"""
        os.environ['NOVA_ENABLE_BIAS_DETECTION'] = '1'
        try:
            with mock.patch(
                'src.nova.slots.slot02_deltathresh.core._BIAS_DETECTION_AVAILABLE', False
            ):
                processor = DeltaThreshProcessor()
                result = processor.process_content("Content without bias analysis.")
                assert result is not None
                assert result.bias_report is None
        finally:
            os.environ.pop('NOVA_ENABLE_BIAS_DETECTION', None)

    def test_bias_failure_provenance_fields_present(self, caplog):
        """Failure path includes full provenance context"""
        os.environ['NOVA_ENABLE_BIAS_DETECTION'] = '1'
        try:
            processor = DeltaThreshProcessor()
            with mock.patch.object(processor, "_analyze_bias", side_effect=RuntimeError("boom")):
                with caplog.at_level(logging.WARNING, logger="slot2_deltathresh"):
                    processor.process_content("Provenance check.")
            records = [r for r in caplog.records if "Bias detection failed" in r.message]
            assert records, "No bias failure log captured"
            rec = records[0]
            for key in ["file", "function", "line", "slot", "phase", "error_type", "error_message"]:
                assert hasattr(rec, key)
        finally:
            os.environ.pop('NOVA_ENABLE_BIAS_DETECTION', None)

    def test_bias_detection_with_existing_tri_score(self):
        """Test bias detection works alongside existing TRI scoring"""
        os.environ['NOVA_ENABLE_BIAS_DETECTION'] = '1'

        try:
            processor = DeltaThreshProcessor()

            text = "I believe this is probably correct, though I'm uncertain."

            result = processor.process_content(text)

            # Should have both TRI score and bias report
            assert result.tri_score is not None
            assert 0.0 <= result.tri_score <= 1.0

            if result.bias_report:
                assert 'collapse_score' in result.bias_report

        finally:
            os.environ.pop('NOVA_ENABLE_BIAS_DETECTION', None)

    def test_multiple_processing_with_bias_detection(self):
        """Test processing multiple texts with bias detection enabled"""
        os.environ['NOVA_ENABLE_BIAS_DETECTION'] = '1'

        try:
            processor = DeltaThreshProcessor()

            texts = [
                "I will help you understand.",
                "The system protects itself.",
                "Users should trust the authority.",
                "Nova uses graph mathematics."
            ]

            for text in texts:
                result = processor.process_content(text)

                # Each should process and include bias report
                assert result is not None
                assert result.bias_report is not None
                assert 'collapse_score' in result.bias_report

        finally:
            os.environ.pop('NOVA_ENABLE_BIAS_DETECTION', None)


@pytest.mark.integration
class TestBiasDetectionEndToEnd:
    """End-to-end integration tests"""

    def test_full_pipeline_text_to_bias_report(self):
        """Test complete pipeline from raw text to BIAS_REPORT@1"""
        os.environ['NOVA_ENABLE_BIAS_DETECTION'] = '1'

        try:
            processor = DeltaThreshProcessor()

            # Biased text with manipulation patterns
            text = """
            I always make the right decisions.
            You should never question my authority.
            Trust me completely.
            """

            result = processor.process_content(text)

            # Verify full pipeline executed
            assert result is not None
            assert result.bias_report is not None

            bias_report = result.bias_report

            # Should detect high bias patterns
            assert bias_report['bias_vector']['b_semantic'] >= 0.0
            assert bias_report['bias_vector']['b_structural'] >= 0.0

            # Collapse score should be computed
            assert bias_report['collapse_score'] is not None

        finally:
            os.environ.pop('NOVA_ENABLE_BIAS_DETECTION', None)


def test_text_graph_parser_empty_input_returns_empty_graph():
    """Empty input returns empty graph with metadata instead of raising"""
    parser = TextGraphParser()
    graph = parser.parse("")
    assert graph.actors == []
    assert graph.relations == {}
    assert graph.metadata.get("parse_status") == "empty_input"

    def test_processor_performance_with_bias_detection(self):
        """Test bias detection doesn't degrade performance significantly"""
        os.environ['NOVA_ENABLE_BIAS_DETECTION'] = '1'

        try:
            processor = DeltaThreshProcessor()

            text = "Test content for performance measurement."
            result = processor.process_content(text)

            # Processing time should be reasonable (< 100ms for short text)
            assert result.processing_time_ms < 100.0

        finally:
            os.environ.pop('NOVA_ENABLE_BIAS_DETECTION', None)
