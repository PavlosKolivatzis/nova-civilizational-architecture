"""
Unit tests for Multi-Slot Consistency (MSC) — Phase 7 Step 6

Tests three conflict detector algorithms:
1. Safety ↔ Production (Slot03 ↔ Slot07)
2. Culture ↔ Deployment (Slot06 ↔ Slot10)
3. Predictive ↔ Production (PTE ↔ Slot07)

Plus composite gap scoring and severity calculation.
"""
import pytest
from nova.orchestrator.predictive.consistency import (
    compute_consistency_gap,
    ConsistencyProfile,
    _compute_safety_production_conflict,
    _compute_culture_deployment_conflict,
    _compute_predictive_production_conflict,
)


class TestSafetyProductionConflict:
    """Test safety-production conflict detection."""

    def test_high_threat_low_pressure_triggers_conflict(self):
        """High threat + low pressure = conflict."""
        slot03 = {"threat_level": 0.8}
        slot07 = {"pressure_level": 0.2}

        conflict = _compute_safety_production_conflict(slot03, slot07)

        assert conflict > 0.5  # Significant conflict
        assert conflict <= 1.0

    def test_categorical_threat_level(self):
        """Should handle categorical threat levels."""
        slot03 = {"threat_level": "HIGH"}
        slot07 = {"pressure_level": 0.3}

        conflict = _compute_safety_production_conflict(slot03, slot07)

        assert conflict > 0.4  # HIGH maps to 0.8

    def test_low_threat_no_conflict(self):
        """Low threat should not trigger conflict."""
        slot03 = {"threat_level": 0.3}
        slot07 = {"pressure_level": 0.1}

        conflict = _compute_safety_production_conflict(slot03, slot07)

        assert conflict == 0.0

    def test_high_threat_high_pressure_no_conflict(self):
        """High threat + high pressure = no conflict (appropriate response)."""
        slot03 = {"threat_level": 0.9}
        slot07 = {"pressure_level": 0.8}

        conflict = _compute_safety_production_conflict(slot03, slot07)

        assert conflict == 0.0  # System responding appropriately

    def test_missing_fields_defaults_zero(self):
        """Missing fields should default to zero (no conflict)."""
        slot03 = {}
        slot07 = {}

        conflict = _compute_safety_production_conflict(slot03, slot07)

        assert conflict == 0.0


class TestCultureDeploymentConflict:
    """Test culture-deployment conflict detection."""

    def test_high_risk_active_deployment_triggers_conflict(self):
        """High residual risk + active deployment = conflict."""
        slot06 = {"residual_risk": 0.7}
        slot10 = {"phase": "deploying"}

        conflict = _compute_culture_deployment_conflict(slot06, slot10)

        assert conflict == 0.7  # Should equal residual risk

    def test_deployment_phases_trigger_conflict(self):
        """All active deployment phases should trigger conflict."""
        slot06 = {"residual_risk": 0.6}

        for phase in ["deploying", "rolling", "active"]:
            slot10 = {"phase": phase}
            conflict = _compute_culture_deployment_conflict(slot06, slot10)
            assert conflict == 0.6

    def test_idle_deployment_no_conflict(self):
        """Idle deployment should not trigger conflict."""
        slot06 = {"residual_risk": 0.8}
        slot10 = {"phase": "idle"}

        conflict = _compute_culture_deployment_conflict(slot06, slot10)

        assert conflict == 0.0

    def test_low_risk_active_deployment_no_conflict(self):
        """Low risk + active deployment = no conflict."""
        slot06 = {"residual_risk": 0.3}
        slot10 = {"phase": "deploying"}

        conflict = _compute_culture_deployment_conflict(slot06, slot10)

        assert conflict == 0.0  # Below threshold (0.5)

    def test_case_insensitive_phases(self):
        """Phase matching should be case-insensitive."""
        slot06 = {"residual_risk": 0.6}
        slot10 = {"phase": "DEPLOYING"}

        conflict = _compute_culture_deployment_conflict(slot06, slot10)

        assert conflict == 0.6


class TestPredictiveProductionConflict:
    """Test predictive-production conflict detection."""

    def test_high_collapse_risk_open_production_triggers_conflict(self):
        """High collapse risk + open production = conflict."""
        predictive = {"collapse_risk": 0.8}
        slot07 = {"mode": "BASELINE", "state": "open"}

        conflict = _compute_predictive_production_conflict(predictive, slot07)

        assert conflict == 0.8  # Should equal collapse risk

    def test_uses_predictive_collapse_risk_fallback(self):
        """Should handle both field names for collapse risk."""
        predictive = {"predictive_collapse_risk": 0.75}
        slot07 = {"mode": "FULL", "state": "open"}

        conflict = _compute_predictive_production_conflict(predictive, slot07)

        assert conflict == 0.75

    def test_baseline_and_full_modes_count_as_open(self):
        """BASELINE and FULL modes should be considered open."""
        predictive = {"collapse_risk": 0.7}

        for mode in ["BASELINE", "FULL"]:
            slot07 = {"mode": mode}
            conflict = _compute_predictive_production_conflict(predictive, slot07)
            assert conflict == 0.7

    def test_low_collapse_risk_no_conflict(self):
        """Low collapse risk should not trigger conflict."""
        predictive = {"collapse_risk": 0.4}
        slot07 = {"mode": "BASELINE"}

        conflict = _compute_predictive_production_conflict(predictive, slot07)

        assert conflict == 0.0  # Below threshold (0.6)

    def test_high_risk_closed_production_no_conflict(self):
        """High risk + closed production = no conflict (appropriate response)."""
        predictive = {"collapse_risk": 0.9}
        slot07 = {"mode": "FROZEN", "state": "closed"}

        conflict = _compute_predictive_production_conflict(predictive, slot07)

        assert conflict == 0.0  # System responding appropriately


class TestCompositeGapScore:
    """Test composite gap score calculation."""

    def test_single_conflict_component(self):
        """Single conflict should contribute to gap score."""
        slot03 = {"threat_level": 0.9}
        slot07 = {"pressure_level": 0.1}

        profile = compute_consistency_gap(
            slot03_state=slot03,
            slot07_state=slot07,
            timestamp=1.0
        )

        assert profile.gap_score > 0.3  # Weighted contribution
        assert profile.severity > 0.6  # Safety conflict is severe

    def test_multiple_conflicts_compound(self):
        """Multiple conflicts should compound gap score."""
        slot03 = {"threat_level": 0.8}
        slot06 = {"residual_risk": 0.7}
        slot07 = {"pressure_level": 0.2}
        slot10 = {"phase": "deploying"}
        predictive = {"collapse_risk": 0.75}

        profile = compute_consistency_gap(
            slot03_state=slot03,
            slot06_state=slot06,
            slot07_state=slot07,
            slot10_state=slot10,
            predictive_snapshot=predictive,
            timestamp=2.0
        )

        # All three components should contribute
        assert profile.gap_score > 0.6
        assert len(profile.components) == 3
        assert all(v > 0.0 for v in profile.components.values())

    def test_severity_equals_worst_component(self):
        """Severity should equal maximum component conflict."""
        slot06 = {"residual_risk": 0.9}  # Worst
        slot07 = {"pressure_level": 0.3}
        slot10 = {"phase": "rolling"}
        predictive = {"collapse_risk": 0.65}  # Lower

        profile = compute_consistency_gap(
            slot06_state=slot06,
            slot07_state=slot07,
            slot10_state=slot10,
            predictive_snapshot=predictive,
            timestamp=3.0
        )

        assert profile.severity == 0.9  # Worst component

    def test_conflicting_slots_list(self):
        """Should list slots involved in conflicts."""
        slot03 = {"threat_level": 0.85}
        slot07 = {"pressure_level": 0.15, "mode": "BASELINE"}
        predictive = {"collapse_risk": 0.7}

        profile = compute_consistency_gap(
            slot03_state=slot03,
            slot07_state=slot07,
            predictive_snapshot=predictive,
            timestamp=4.0
        )

        # Both safety-prod and predictive-prod conflicts
        assert "slot03" in profile.conflicting_slots
        assert "slot07" in profile.conflicting_slots
        assert "predictive" in profile.conflicting_slots

    def test_pattern_alerts_tracked(self):
        """Should track EPD patterns that contributed."""
        alerts = [
            {"type": "governance_oscillation", "severity": 0.6},
            {"type": "predictive_creep", "severity": 0.8},
        ]

        profile = compute_consistency_gap(
            pattern_alerts=alerts,
            timestamp=5.0
        )

        # Only high-severity patterns (> 0.5)
        assert "governance_oscillation" in profile.caused_by
        assert "predictive_creep" in profile.caused_by

    def test_no_conflicts_returns_zero_gap(self):
        """No conflicts should result in zero gap score."""
        slot03 = {"threat_level": 0.2}
        slot06 = {"residual_risk": 0.3}
        slot07 = {"pressure_level": 0.8, "mode": "FROZEN"}
        slot10 = {"phase": "idle"}
        predictive = {"collapse_risk": 0.3}

        profile = compute_consistency_gap(
            slot03_state=slot03,
            slot06_state=slot06,
            slot07_state=slot07,
            slot10_state=slot10,
            predictive_snapshot=predictive,
            timestamp=6.0
        )

        assert profile.gap_score == 0.0
        assert profile.severity == 0.0
        assert len(profile.conflicting_slots) == 0


class TestConsistencyProfileSerialization:
    """Test ConsistencyProfile contract serialization."""

    def test_to_dict_format(self):
        """Should serialize to predictive_consistency_gap@1 contract format."""
        profile = ConsistencyProfile(
            gap_score=0.75,
            components={
                "safety_production_conflict": 0.6,
                "culture_deployment_conflict": 0.8,
                "production_predictive_conflict": 0.7
            },
            conflicting_slots=["slot03", "slot07", "slot10"],
            severity=0.8,
            caused_by=["predictive_creep"],
            source_snapshot_hash="abc123",
            timestamp=10.0
        )

        data = profile.to_dict()

        assert data["score"] == 0.75
        assert "components" in data
        assert data["severity"] == 0.8
        assert data["conflicting_slots"] == ["slot03", "slot07", "slot10"]
        assert data["caused_by"] == ["predictive_creep"]
        assert data["timestamp"] == 10.0
