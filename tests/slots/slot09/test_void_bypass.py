"""
Slot09 VOID Bypass Tests

Phase 14.4: RFC-014 Slot09 distortion filter bypass for VOID state.
Tests that VOID (empty SystemGraph) passes through without distortion alerts.
"""

import pytest
from src.nova.slots.slot09_distortion_protection.void_bypass import (
    is_void_state,
    create_void_passthrough_response,
    should_bypass_distortion_check,
    get_void_metrics
)


class TestVOIDStateDetection:
    """Test VOID state identification (RFC-014 § 3.2)"""

    def test_is_void_state_true(self):
        """graph_state='void' → True"""
        assert is_void_state('void') is True

    def test_is_void_state_false(self):
        """graph_state='normal' → False"""
        assert is_void_state('normal') is False
        assert is_void_state('unknown') is False
        assert is_void_state(None) is False
        assert is_void_state('') is False

    def test_should_bypass_direct_graph_state(self):
        """Direct graph_state parameter triggers bypass"""
        assert should_bypass_distortion_check(graph_state='void') is True
        assert should_bypass_distortion_check(graph_state='normal') is False

    def test_should_bypass_from_bias_report(self):
        """Extract graph_state from BIAS_REPORT@1 metadata"""
        bias_report_void = {
            'metadata': {'graph_state': 'void'}
        }
        assert should_bypass_distortion_check(bias_report=bias_report_void) is True

        bias_report_normal = {
            'metadata': {'graph_state': 'normal'}
        }
        assert should_bypass_distortion_check(bias_report=bias_report_normal) is False

    def test_should_bypass_no_void_mode_flag(self, monkeypatch):
        """NOVA_ENABLE_VOID_MODE=0 → no bypass"""
        monkeypatch.setenv("NOVA_ENABLE_VOID_MODE", "0")
        assert should_bypass_distortion_check(graph_state='void') is False


class TestVOIDPassthroughResponse:
    """Test VOID passthrough response generation"""

    def test_void_response_structure(self):
        """VOID response has correct structure"""
        response = create_void_passthrough_response({}, "test_trace")

        assert response['final_policy'] == 'STANDARD_PROCESSING'
        assert response['distortion_score'] == 0.0
        assert response['confidence'] == 1.0
        assert response['spectral_filter_disabled'] is True
        assert response['threat_level'] == 0.0

    def test_void_response_rationale(self):
        """VOID response includes rationale"""
        response = create_void_passthrough_response({}, "test_trace")

        assert 'analysis' in response
        assert response['analysis']['graph_state'] == 'void'
        assert 'ontologically valid' in response['analysis']['rationale']

    def test_void_response_metadata(self):
        """VOID response includes RFC-014 metadata"""
        response = create_void_passthrough_response({}, "test_trace_123")

        assert response['metadata']['void_bypass'] is True
        assert response['metadata']['rfc'] == 'RFC-014'
        assert response['metadata']['trace_id'] == 'test_trace_123'

    def test_void_metric_incremented(self):
        """VOID passthrough increments metric"""
        from src.nova.slots.slot09_distortion_protection.void_bypass import _void_passthrough_counter

        initial_count = _void_passthrough_counter._value._value

        create_void_passthrough_response({}, "metric_test")

        assert _void_passthrough_counter._value._value == initial_count + 1

    def test_void_response_spectral_entropy_zero(self):
        """VOID analysis shows H=0 (expected for empty graph)"""
        response = create_void_passthrough_response({}, "test")

        assert response['analysis']['spectral_entropy'] == 0.0

    def test_void_response_equilibrium_none(self):
        """VOID analysis shows ρ=None (undefined for empty graph)"""
        response = create_void_passthrough_response({}, "test")

        assert response['analysis']['equilibrium_ratio'] is None


class TestVOIDMetrics:
    """Test VOID bypass observability"""

    def test_get_void_metrics(self):
        """get_void_metrics() returns passthrough count"""
        metrics = get_void_metrics()

        assert 'void_passthrough_total' in metrics
        assert isinstance(metrics['void_passthrough_total'], (int, float))


class TestVOIDNonInterference:
    """Test VOID bypass doesn't affect non-VOID processing"""

    def test_non_void_no_bypass(self):
        """graph_state='normal' → no bypass"""
        assert should_bypass_distortion_check(graph_state='normal') is False

    def test_missing_graph_state_no_bypass(self):
        """Missing graph_state → no bypass"""
        assert should_bypass_distortion_check() is False

    def test_empty_bias_report_no_bypass(self):
        """Empty bias_report → no bypass"""
        assert should_bypass_distortion_check(bias_report={}) is False

    def test_bias_report_no_metadata_no_bypass(self):
        """bias_report without metadata → no bypass"""
        bias_report = {'bias_vector': {}, 'collapse_score': 0.2}
        assert should_bypass_distortion_check(bias_report=bias_report) is False
