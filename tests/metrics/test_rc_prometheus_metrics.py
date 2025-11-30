"""
Tests for Phase 7.0-RC Step 5: Prometheus Metrics

Validates RC monitoring metrics export correctly to Prometheus.
"""

import pytest
import time
from nova.orchestrator.prometheus_metrics import (
    record_memory_resonance,
    record_ris,
    record_stress_recovery,
    record_rc_criteria,
    memory_stability_gauge,
    memory_samples_gauge,
    memory_volatility_gauge,
    memory_trend_gauge,
    ris_score_gauge,
    ris_component_gauge,
    stress_recovery_rate_gauge,
    stress_baseline_gauge,
    stress_recovery_ticks_gauge,
    stress_max_deviation_gauge,
    stress_last_run_gauge,
    rc_gate_status_gauge,
    rc_overall_pass_gauge,
)


class TestMemoryResonanceMetrics:
    """Test memory resonance Prometheus metrics."""

    def test_record_memory_resonance_all_fields(self):
        """Should record all memory resonance fields to gauges."""
        stats = {
            "stability": 0.85,
            "count": 168,
            "stdev": 0.05,
            "trend_24h": 0.02
        }

        record_memory_resonance(stats)

        # Verify gauges updated
        assert memory_stability_gauge._value._value == 0.85
        assert memory_samples_gauge._value._value == 168
        assert memory_volatility_gauge._value._value == 0.05
        assert memory_trend_gauge._value._value == 0.02

    def test_record_memory_resonance_clamping(self):
        """Should clamp stability and volatility to [0.0, 1.0]."""
        stats = {
            "stability": 1.5,  # Above 1.0
            "count": 100,
            "stdev": -0.1,  # Below 0.0
            "trend_24h": 0.0
        }

        record_memory_resonance(stats)

        assert memory_stability_gauge._value._value == 1.0  # Clamped
        assert memory_volatility_gauge._value._value == 0.0  # Clamped

    def test_record_memory_resonance_default_values(self):
        """Should use default values for missing keys."""
        stats = {}  # Empty stats

        record_memory_resonance(stats)

        assert memory_stability_gauge._value._value == 0.5  # Default
        assert memory_samples_gauge._value._value == 0
        assert memory_volatility_gauge._value._value == 0.0
        assert memory_trend_gauge._value._value == 0.0


class TestRISMetrics:
    """Test RIS Prometheus metrics."""

    def test_record_ris_composite_and_components(self):
        """Should record RIS composite and labeled components."""
        record_ris(ris_score=0.90, memory_stability=0.85, ethics_score=1.0)

        # Verify composite gauge
        assert ris_score_gauge._value._value == 0.90

        # Verify component gauges (labeled)
        memory_label = ris_component_gauge.labels(component_type="memory_stability")
        assert memory_label._value._value == 0.85

        ethics_label = ris_component_gauge.labels(component_type="ethics_compliance")
        assert ethics_label._value._value == 1.0

    def test_record_ris_clamping(self):
        """Should clamp all RIS values to [0.0, 1.0]."""
        record_ris(ris_score=1.2, memory_stability=1.5, ethics_score=-0.1)

        assert ris_score_gauge._value._value == 1.0  # Clamped
        assert ris_component_gauge.labels(component_type="memory_stability")._value._value == 1.0
        assert ris_component_gauge.labels(component_type="ethics_compliance")._value._value == 0.0


class TestStressRecoveryMetrics:
    """Test stress simulation Prometheus metrics."""

    def test_record_stress_recovery_all_fields(self):
        """Should record all stress recovery metrics."""
        metrics = {
            "recovery_rate": 0.95,
            "baseline_ris": 0.88,
            "recovery_time_hours": 12,
            "max_deviation": 0.15,
            "timestamp": 1234567890.0
        }

        record_stress_recovery(metrics)

        assert stress_recovery_rate_gauge._value._value == 0.95
        assert stress_baseline_gauge._value._value == 0.88
        assert stress_recovery_ticks_gauge._value._value == 12
        assert stress_max_deviation_gauge._value._value == 0.15
        assert stress_last_run_gauge._value._value == 1234567890.0

    def test_record_stress_recovery_clamping(self):
        """Should clamp rate, baseline, and deviation to [0.0, 1.0]."""
        metrics = {
            "recovery_rate": 1.5,
            "baseline_ris": -0.1,
            "recovery_time_hours": 24,
            "max_deviation": 2.0,
            "timestamp": time.time()
        }

        record_stress_recovery(metrics)

        assert stress_recovery_rate_gauge._value._value == 1.0
        assert stress_baseline_gauge._value._value == 0.0
        assert stress_max_deviation_gauge._value._value == 1.0

    def test_record_stress_recovery_default_timestamp(self):
        """Should use current time if timestamp missing."""
        before_time = time.time()

        metrics = {
            "recovery_rate": 0.90,
            "baseline_ris": 0.85,
            "recovery_time_hours": 18,
            "max_deviation": 0.10
        }

        record_stress_recovery(metrics)

        after_time = time.time()

        # Timestamp should be between before and after
        recorded_time = stress_last_run_gauge._value._value
        assert before_time <= recorded_time <= after_time


class TestRCCriteriaMetrics:
    """Test RC criteria gate Prometheus metrics."""

    def test_record_rc_criteria_all_pass(self):
        """Should set all gates to 1.0 when passing."""
        criteria = {
            "memory_stability_pass": True,
            "ris_pass": True,
            "stress_recovery_pass": True,
            "samples_sufficient": True,
            "overall_pass": True
        }

        record_rc_criteria(criteria)

        # Individual gates
        assert rc_gate_status_gauge.labels(gate_name="memory_stability")._value._value == 1.0
        assert rc_gate_status_gauge.labels(gate_name="ris_score")._value._value == 1.0
        assert rc_gate_status_gauge.labels(gate_name="stress_recovery")._value._value == 1.0
        assert rc_gate_status_gauge.labels(gate_name="samples_sufficient")._value._value == 1.0

        # Overall
        assert rc_overall_pass_gauge._value._value == 1.0

    def test_record_rc_criteria_all_fail(self):
        """Should set all gates to 0.0 when failing."""
        criteria = {
            "memory_stability_pass": False,
            "ris_pass": False,
            "stress_recovery_pass": False,
            "samples_sufficient": False,
            "overall_pass": False
        }

        record_rc_criteria(criteria)

        # Individual gates
        assert rc_gate_status_gauge.labels(gate_name="memory_stability")._value._value == 0.0
        assert rc_gate_status_gauge.labels(gate_name="ris_score")._value._value == 0.0
        assert rc_gate_status_gauge.labels(gate_name="stress_recovery")._value._value == 0.0
        assert rc_gate_status_gauge.labels(gate_name="samples_sufficient")._value._value == 0.0

        # Overall
        assert rc_overall_pass_gauge._value._value == 0.0

    def test_record_rc_criteria_mixed_results(self):
        """Should handle mixed pass/fail correctly."""
        criteria = {
            "memory_stability_pass": True,
            "ris_pass": True,
            "stress_recovery_pass": False,  # Failed
            "samples_sufficient": True,
            "overall_pass": False  # Overall fails if any gate fails
        }

        record_rc_criteria(criteria)

        assert rc_gate_status_gauge.labels(gate_name="memory_stability")._value._value == 1.0
        assert rc_gate_status_gauge.labels(gate_name="ris_score")._value._value == 1.0
        assert rc_gate_status_gauge.labels(gate_name="stress_recovery")._value._value == 0.0
        assert rc_gate_status_gauge.labels(gate_name="samples_sufficient")._value._value == 1.0
        assert rc_overall_pass_gauge._value._value == 0.0


class TestMetricsIntegration:
    """Test integrated metrics recording scenarios."""

    def test_full_rc_validation_metrics_passing(self):
        """Simulate full RC validation with passing metrics."""
        # Memory resonance
        record_memory_resonance({
            "stability": 0.85,
            "count": 168,
            "stdev": 0.05,
            "trend_24h": 0.02
        })

        # RIS
        record_ris(ris_score=0.90, memory_stability=0.85, ethics_score=1.0)

        # Stress recovery
        record_stress_recovery({
            "recovery_rate": 0.95,
            "baseline_ris": 0.88,
            "recovery_time_hours": 12,
            "max_deviation": 0.10,
            "timestamp": time.time()
        })

        # RC criteria
        record_rc_criteria({
            "memory_stability_pass": True,
            "ris_pass": True,
            "stress_recovery_pass": True,
            "samples_sufficient": True,
            "overall_pass": True
        })

        # Verify all metrics recorded
        assert memory_stability_gauge._value._value == 0.85
        assert ris_score_gauge._value._value == 0.90
        assert stress_recovery_rate_gauge._value._value == 0.95
        assert rc_overall_pass_gauge._value._value == 1.0

    def test_full_rc_validation_metrics_failing(self):
        """Simulate full RC validation with failing metrics."""
        # Memory resonance (below threshold)
        record_memory_resonance({
            "stability": 0.75,  # Below 0.80 threshold
            "count": 168,
            "stdev": 0.08,
            "trend_24h": -0.05
        })

        # RIS (below threshold)
        record_ris(ris_score=0.70, memory_stability=0.75, ethics_score=1.0)

        # Stress recovery (below threshold)
        record_stress_recovery({
            "recovery_rate": 0.85,  # Below 0.90 threshold
            "baseline_ris": 0.88,
            "recovery_time_hours": 24,
            "max_deviation": 0.20,
            "timestamp": time.time()
        })

        # RC criteria (failing)
        record_rc_criteria({
            "memory_stability_pass": False,
            "ris_pass": False,
            "stress_recovery_pass": False,
            "samples_sufficient": True,
            "overall_pass": False
        })

        # Verify all metrics recorded
        assert memory_stability_gauge._value._value == 0.75
        assert ris_score_gauge._value._value == 0.70
        assert stress_recovery_rate_gauge._value._value == 0.85
        assert rc_overall_pass_gauge._value._value == 0.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
