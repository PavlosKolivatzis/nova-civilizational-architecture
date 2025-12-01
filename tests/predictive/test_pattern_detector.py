"""
Unit tests for Emergent Pattern Detector (EPD) — Phase 7 Step 5

Tests three pattern types:
1. Governance oscillation (allow/hold toggling)
2. Predictive creep (monotonic drift increase)
3. Escalation loop (repeated router penalties)

Plus debouncing, boundary cases, and negative scenarios.
"""
import pytest
from nova.orchestrator.predictive.pattern_detector import detect_patterns, PatternAlert


class TestGovernanceOscillation:
    """Test governance oscillation pattern detection."""

    def test_detects_oscillation_at_threshold(self):
        """3 toggles = threshold, should detect with severity 0.0."""
        history = [
            {"timestamp": float(i), "allowed": i % 2 == 0}
            for i in range(10)
        ]
        # Pattern: T F T F T F T F T F = 9 transitions (exceeds threshold)

        alerts = detect_patterns([], history, [], window_size=10)

        assert len(alerts) == 1
        alert = alerts[0]
        assert alert.pattern_type == "governance_oscillation"
        assert alert.severity >= 0.0
        assert alert.metadata["toggle_count"] >= 3

    def test_no_oscillation_below_threshold(self):
        """Less than 3 toggles should not trigger."""
        history = [
            {"timestamp": 1.0, "allowed": True},
            {"timestamp": 2.0, "allowed": True},
            {"timestamp": 3.0, "allowed": False},
            {"timestamp": 4.0, "allowed": False},
        ]
        # Only 1 transition (True→False)

        alerts = detect_patterns([], history, [], window_size=10)

        assert len(alerts) == 0

    def test_severity_increases_with_toggles(self):
        """More toggles should increase severity."""
        # Create 10 toggles (very high oscillation)
        history = [
            {"timestamp": float(i), "allowed": i % 2 == 0}
            for i in range(12)
        ]

        alerts = detect_patterns([], history, [], window_size=12)

        assert len(alerts) == 1
        alert = alerts[0]
        assert alert.severity > 0.5  # High severity
        assert alert.metadata["toggle_count"] >= 10

    def test_handles_missing_allowed_field(self):
        """Should tolerate entries without 'allowed' field."""
        history = [
            {"timestamp": 1.0},  # Missing 'allowed'
            {"timestamp": 2.0, "allowed": True},
            {"timestamp": 3.0, "allowed": False},
            {"timestamp": 4.0},  # Missing 'allowed'
        ]

        # Should not crash, uses default True for missing fields
        alerts = detect_patterns([], history, [], window_size=10)
        # May or may not detect pattern depending on defaults


class TestPredictiveCreep:
    """Test predictive creep pattern detection."""

    def test_detects_monotonic_increase(self):
        """Monotonic drift velocity increase should trigger."""
        history = [
            {
                "timestamp": float(i),
                "tri_coherence": 0.8,
                "tri_drift_z": float(i),
                "drift_velocity": 0.1 * (i + 1),  # Monotonic increase
            }
            for i in range(10)
        ]

        alerts = detect_patterns(history, [], [], window_size=10)

        assert len(alerts) == 1
        alert = alerts[0]
        assert alert.pattern_type == "predictive_creep"
        assert alert.severity > 0.0
        assert alert.metadata["monotonic_runs"] == 5
        assert alert.metadata["final_velocity"] > alert.metadata["velocity_delta"]

    def test_no_creep_with_low_coherence(self):
        """Should not trigger if coherence < 0.7 (unstable regime)."""
        history = [
            {
                "timestamp": float(i),
                "tri_coherence": 0.5,  # Below threshold
                "drift_velocity": 0.1 * (i + 1),
            }
            for i in range(10)
        ]

        alerts = detect_patterns(history, [], [], window_size=10)

        assert len(alerts) == 0

    def test_no_creep_with_non_monotonic(self):
        """Should not trigger if velocity oscillates."""
        history = [
            {
                "timestamp": float(i),
                "tri_coherence": 0.8,
                "tri_drift_z": float(i),
                "drift_velocity": 0.5 if i % 2 == 0 else 0.2,  # Oscillating
            }
            for i in range(10)
        ]

        alerts = detect_patterns(history, [], [], window_size=10)

        assert len(alerts) == 0

    def test_severity_scales_with_velocity(self):
        """Higher final velocity should increase severity."""
        history = [
            {
                "timestamp": float(i),
                "tri_coherence": 0.9,
                "tri_drift_z": float(i),
                "drift_velocity": 0.5 * (i + 1),  # High velocity
            }
            for i in range(10)
        ]

        alerts = detect_patterns(history, [], [], window_size=10)

        assert len(alerts) == 1
        alert = alerts[0]
        assert alert.severity > 0.5  # Should be high severity


class TestEscalationLoop:
    """Test escalation loop pattern detection."""

    def test_detects_repeated_penalties(self):
        """Same route penalized ≥4 times should trigger."""
        history = [
            {
                "timestamp": float(i),
                "route": "slot_X",
                "penalty": 0.3,
                "stability_pressure": 1.0,  # Low pressure
            }
            for i in range(6)
        ]

        alerts = detect_patterns([], [], history, window_size=10)

        assert len(alerts) == 1
        alert = alerts[0]
        assert alert.pattern_type == "escalation_loop"
        assert alert.severity > 0.0
        assert alert.metadata["penalty_count"] == 6
        assert alert.metadata["affected_route"] == "slot_X"

    def test_no_escalation_below_threshold(self):
        """Less than 4 penalties should not trigger."""
        history = [
            {
                "timestamp": float(i),
                "route": "slot_X",
                "penalty": 0.3,
                "stability_pressure": 1.0,
            }
            for i in range(3)
        ]

        alerts = detect_patterns([], [], history, window_size=10)

        assert len(alerts) == 0

    def test_no_escalation_with_high_pressure(self):
        """Should not trigger if pressure ≥2.0 (justified penalties)."""
        history = [
            {
                "timestamp": float(i),
                "route": "slot_X",
                "penalty": 0.3,
                "stability_pressure": 3.0,  # High pressure = justified
            }
            for i in range(6)
        ]

        alerts = detect_patterns([], [], history, window_size=10)

        assert len(alerts) == 0

    def test_handles_missing_fields(self):
        """Should tolerate missing penalty/pressure fields (GPT-5.1 robustness)."""
        history = [
            {"timestamp": 1.0, "route": "slot_X"},  # Missing penalty/pressure
            {"timestamp": 2.0, "route": "slot_X", "penalty": 0.3},  # Missing pressure
            {"timestamp": 3.0, "route": "slot_X", "stability_pressure": 1.0},  # Missing penalty
        ]

        # Should not crash
        alerts = detect_patterns([], [], history, window_size=10)


class TestMultiplePatterns:
    """Test concurrent pattern detection."""

    def test_detects_multiple_patterns_simultaneously(self):
        """Should detect oscillation + creep + escalation concurrently."""
        gov_history = [
            {"timestamp": float(i), "allowed": i % 2 == 0}
            for i in range(10)
        ]
        pred_history = [
            {
                "timestamp": float(i),
                "tri_coherence": 0.8,
                "tri_drift_z": float(i),
                "drift_velocity": 0.2 * (i + 1),
            }
            for i in range(10)
        ]
        router_history = [
            {
                "timestamp": float(i),
                "route": "slot_Y",
                "penalty": 0.5,
                "stability_pressure": 0.8,
            }
            for i in range(6)
        ]

        alerts = detect_patterns(pred_history, gov_history, router_history, window_size=10)

        # Should detect all three patterns
        assert len(alerts) == 3
        types = {alert.pattern_type for alert in alerts}
        assert "governance_oscillation" in types
        assert "predictive_creep" in types
        assert "escalation_loop" in types


class TestBoundaryCases:
    """Test edge cases and boundary conditions."""

    def test_empty_history(self):
        """Empty history should return no alerts."""
        alerts = detect_patterns([], [], [], window_size=10)
        assert len(alerts) == 0

    def test_insufficient_history(self):
        """History with < 5 entries should not trigger patterns."""
        history = [{"timestamp": float(i)} for i in range(3)]

        alerts = detect_patterns(history, history, history, window_size=10)
        assert len(alerts) == 0

    def test_window_size_limits_analysis(self):
        """Should only analyze last N entries per window_size."""
        # Create long history where only recent entries show pattern
        history = [
            {"timestamp": float(i), "allowed": True}
            for i in range(50)
        ] + [
            {"timestamp": float(50 + i), "allowed": i % 2 == 0}
            for i in range(10)
        ]

        # Small window should only see recent oscillation
        alerts = detect_patterns([], history, [], window_size=15)

        assert len(alerts) == 1  # Only recent pattern detected

    def test_pattern_at_window_boundary(self):
        """Pattern spanning window edge should trigger exactly once."""
        history = [
            {"timestamp": float(i), "allowed": i % 2 == 0}
            for i in range(20)
        ]

        # Detect with window that cuts through oscillations
        alerts = detect_patterns([], history, [], window_size=10)

        assert len(alerts) == 1  # Should fire once, not multiple times
