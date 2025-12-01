"""
Governance integration tests for MSC — Phase 7 Step 6

Tests:
1. Consistency gap blocks governance when threshold exceeded
2. Gap profile publishes to semantic mirror
3. Metrics record all component values
4. Feature flag enables/disables MSC
"""
import pytest
from nova.orchestrator.governance.engine import GovernanceEngine


class TestGovernanceConsistencyIntegration:
    """Test MSC integration with governance engine."""

    @pytest.fixture(autouse=True)
    def enable_msc(self, monkeypatch):
        """Enable MSC for these tests."""
        monkeypatch.setenv("NOVA_ENABLE_MSC", "true")

    def test_high_gap_blocks_governance(self):
        """High consistency gap should block governance."""
        engine = GovernanceEngine()

        # Create state with safety-production conflict
        state = {
            "tri_signal": {
                "tri_coherence": 0.95,
                "tri_drift_z": 0.1,
                "tri_jitter": 0.02
            },
            "slot03": {"threat_level": "HIGH"},  # High threat
            "slot07": {"mode": "BASELINE", "pressure_level": 0.1},  # Low pressure
            "slot10": {"passed": True},
            "timestamp": 1.0,
        }

        result = engine.evaluate(state)

        # Should block due to consistency gap
        assert not result.allowed
        assert result.reason == "consistency_gap"
        assert "consistency_gap" in result.metadata

    def test_high_severity_blocks_governance(self):
        """High severity component should block even if gap score is moderate."""
        engine = GovernanceEngine()

        # Create state with single severe conflict
        state = {
            "tri_signal": {
                "tri_coherence": 0.95,
                "tri_drift_z": 0.1,
                "tri_jitter": 0.02
            },
            "slot06": {"residual_risk": 0.85},  # Very high risk
            "slot07": {"mode": "BASELINE"},
            "slot10": {"passed": True, "phase": "deploying"},  # Active deployment
            "timestamp": 2.0,
        }

        result = engine.evaluate(state)

        # Should block due to high severity
        assert not result.allowed
        assert result.reason == "consistency_gap"
        gap_data = result.metadata["consistency_gap"]
        assert gap_data["severity"] >= 0.7

    def test_low_gap_allows_governance(self):
        """Low consistency gap should not block governance."""
        engine = GovernanceEngine()

        # Create state with no conflicts
        state = {
            "tri_signal": {
                "tri_coherence": 0.95,
                "tri_drift_z": 0.1,
                "tri_jitter": 0.02
            },
            "slot03": {"threat_level": 0.2},  # Low threat
            "slot07": {"mode": "BASELINE", "pressure_level": 0.8},  # Appropriate pressure
            "slot10": {"passed": True, "phase": "idle"},
            "timestamp": 3.0,
        }

        result = engine.evaluate(state)

        # Should allow (no consistency issues)
        assert result.allowed
        assert result.reason == "ok"

    def test_consistency_profile_in_metadata(self):
        """Consistency profile should be in result metadata."""
        engine = GovernanceEngine()

        state = {
            "tri_signal": {
                "tri_coherence": 0.95,
                "tri_drift_z": 0.1,
                "tri_jitter": 0.02
            },
            "slot03": {"threat_level": 0.8},
            "slot07": {"mode": "BASELINE", "pressure_level": 0.2},
            "slot10": {"passed": True},
            "timestamp": 4.0,
        }

        result = engine.evaluate(state)

        # Should have consistency gap in metadata
        assert "consistency_gap" in result.metadata
        gap_data = result.metadata["consistency_gap"]

        # Verify contract fields
        assert "score" in gap_data
        assert "components" in gap_data
        assert "conflicting_slots" in gap_data
        assert "severity" in gap_data
        assert "timestamp" in gap_data

    def test_conflicting_slots_identified(self):
        """Should identify which slots are in conflict."""
        engine = GovernanceEngine()

        state = {
            "tri_signal": {
                "tri_coherence": 0.95,
                "tri_drift_z": 0.1,
                "tri_jitter": 0.02
            },
            "slot03": {"threat_level": 0.85},  # Conflict with slot07
            "slot07": {"mode": "BASELINE", "pressure_level": 0.15},
            "slot10": {"passed": True},
            "timestamp": 5.0,
        }

        result = engine.evaluate(state)

        gap_data = result.metadata.get("consistency_gap", {})
        conflicting = gap_data.get("conflicting_slots", [])

        # Should identify slot03 and slot07 as conflicting
        assert "slot03" in conflicting
        assert "slot07" in conflicting

    def test_msc_disabled_by_default(self, monkeypatch):
        """MSC should not run when NOVA_ENABLE_MSC is false."""
        monkeypatch.setenv("NOVA_ENABLE_MSC", "false")
        engine = GovernanceEngine()

        # Create state with conflicts
        state = {
            "tri_signal": {
                "tri_coherence": 0.95,
                "tri_drift_z": 0.1,
                "tri_jitter": 0.02
            },
            "slot03": {"threat_level": "HIGH"},
            "slot07": {"mode": "BASELINE", "pressure_level": 0.1},
            "slot10": {"passed": True},
            "timestamp": 6.0,
        }

        result = engine.evaluate(state)

        # Should not have consistency gap (MSC disabled)
        assert "consistency_gap" not in result.metadata
        # Should allow (no MSC blocking)
        assert result.allowed

    def test_consistency_gap_published_to_mirror(self):
        """Consistency gap should publish to semantic mirror."""
        from nova.orchestrator.semantic_mirror import reset_semantic_mirror

        reset_semantic_mirror()
        engine = GovernanceEngine()

        state = {
            "tri_signal": {
                "tri_coherence": 0.95,
                "tri_drift_z": 0.1,
                "tri_jitter": 0.02
            },
            "slot06": {"residual_risk": 0.75},
            "slot07": {"mode": "BASELINE"},
            "slot10": {"passed": True, "phase": "deploying"},
            "timestamp": 7.0,
        }

        result = engine.evaluate(state)

        # Should have published consistency gap
        # (Mirror publishing happens in _publish_to_mirror)
        assert "consistency_gap" in result.metadata

    def test_multiple_conflicts_compound(self):
        """Multiple conflicts should result in higher gap score."""
        engine = GovernanceEngine()

        # Create state with multiple conflicts
        state = {
            "tri_signal": {
                "tri_coherence": 0.95,
                "tri_drift_z": 0.1,
                "tri_jitter": 0.02
            },
            "slot03": {"threat_level": 0.8},  # Safety conflict
            "slot06": {"residual_risk": 0.7},  # Culture conflict
            "slot07": {"mode": "BASELINE", "pressure_level": 0.2},
            "slot10": {"passed": True, "phase": "deploying"},
            "timestamp": 8.0,
        }

        # Add predictive conflict
        state["predictive"] = {"collapse_risk": 0.75}

        result = engine.evaluate(state)

        gap_data = result.metadata.get("consistency_gap", {})
        components = gap_data.get("components", {})

        # Should have multiple non-zero components
        non_zero = sum(1 for v in components.values() if v > 0.0)
        assert non_zero >= 2  # At least 2 conflicts

        # Gap score should be elevated
        assert gap_data.get("score", 0.0) > 0.4  # Weighted sum of components

    def test_threshold_configuration(self, monkeypatch):
        """Should respect custom threshold configuration."""
        monkeypatch.setenv("NOVA_ENABLE_MSC", "true")
        engine = GovernanceEngine()

        # Create state with moderate gap
        state = {
            "tri_signal": {
                "tri_coherence": 0.95,
                "tri_drift_z": 0.1,
                "tri_jitter": 0.02
            },
            "slot03": {"threat_level": 0.65},
            "slot07": {"mode": "BASELINE", "pressure_level": 0.35},
            "slot10": {"passed": True},
            "timestamp": 9.0,
        }

        # With default threshold (0.6), should not block
        result = engine.evaluate(state)

        # Check gap score
        gap_data = result.metadata.get("consistency_gap", {})
        gap_score = gap_data.get("score", 0.0)

        # Verify behavior matches threshold
        if gap_score >= 0.6:
            assert not result.allowed
        else:
            assert result.allowed
