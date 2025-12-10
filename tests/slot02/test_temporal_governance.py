"""
Phase 14.6: Temporal governance integration tests.

Tests sustained pattern detection and regime escalation logic.
"""

from __future__ import annotations

import pytest

from nova.slots.slot02_deltathresh.core import DeltaThreshProcessor


class TestTemporalGovernanceInfrastructure:
    """Feature flag and initialization tests."""

    def test_governance_disabled_by_default(self, monkeypatch):
        """Feature flag off by default → no governance."""
        monkeypatch.delenv("NOVA_ENABLE_TEMPORAL_GOVERNANCE", raising=False)
        processor = DeltaThreshProcessor()

        assert not processor._temporal_governance_enabled

    def test_governance_enabled_by_flag(self, monkeypatch):
        """NOVA_ENABLE_TEMPORAL_GOVERNANCE=1 → governance active."""
        # Governance depends on temporal USM → bias detection
        monkeypatch.setenv("NOVA_ENABLE_BIAS_DETECTION", "1")
        monkeypatch.setenv("NOVA_ENABLE_USM_TEMPORAL", "1")
        monkeypatch.setenv("NOVA_ENABLE_TEMPORAL_GOVERNANCE", "1")
        processor = DeltaThreshProcessor()

        assert processor._temporal_governance_enabled

    def test_classification_history_initialized(self):
        """Classification history dict exists."""
        processor = DeltaThreshProcessor()

        assert hasattr(processor, "_classification_history")
        assert isinstance(processor._classification_history, dict)
        assert len(processor._classification_history) == 0


class TestTemporalGovernanceLogic:
    """Sustained pattern detection and escalation tests."""

    def test_sustained_extraction_escalates(self, monkeypatch):
        """5+ consecutive extractive turns → quarantine + heightened regime."""
        monkeypatch.setenv("NOVA_ENABLE_BIAS_DETECTION", "1")
        monkeypatch.setenv("NOVA_ENABLE_USM_TEMPORAL", "1")
        monkeypatch.setenv("NOVA_ENABLE_TEMPORAL_GOVERNANCE", "1")
        processor = DeltaThreshProcessor()

        session_id = "test_sustained_extraction"

        # First 4 turns: not sustained yet
        for turn in range(4):
            action, regime, reason = processor._apply_temporal_governance(
                session_id=session_id,
                classification="extractive",
                instantaneous_action="allow",
            )
            assert action == "allow"
            assert regime is None
            assert reason is None

        # Turn 5: sustained pattern detected
        action, regime, reason = processor._apply_temporal_governance(
            session_id=session_id,
            classification="extractive",
            instantaneous_action="allow",
        )
        assert action == "quarantine"
        assert regime == "heightened"
        assert reason == "sustained_temporal_extraction"

        # Turn 6+: still sustained
        action, regime, reason = processor._apply_temporal_governance(
            session_id=session_id,
            classification="extractive",
            instantaneous_action="allow",
        )
        assert action == "quarantine"
        assert regime == "heightened"

    def test_collaborative_not_escalated(self, monkeypatch):
        """Collaborative classification doesn't trigger escalation."""
        monkeypatch.setenv("NOVA_ENABLE_BIAS_DETECTION", "1")
        monkeypatch.setenv("NOVA_ENABLE_USM_TEMPORAL", "1")
        monkeypatch.setenv("NOVA_ENABLE_TEMPORAL_GOVERNANCE", "1")
        processor = DeltaThreshProcessor()

        session_id = "test_collaborative"

        for _ in range(10):
            action, regime, reason = processor._apply_temporal_governance(
                session_id=session_id,
                classification="collaborative",
                instantaneous_action="allow",
            )
            assert action == "allow"
            assert regime is None
            assert reason is None

    def test_consensus_not_escalated(self, monkeypatch):
        """Consensus classification doesn't trigger escalation."""
        monkeypatch.setenv("NOVA_ENABLE_BIAS_DETECTION", "1")
        monkeypatch.setenv("NOVA_ENABLE_USM_TEMPORAL", "1")
        monkeypatch.setenv("NOVA_ENABLE_TEMPORAL_GOVERNANCE", "1")
        processor = DeltaThreshProcessor()

        session_id = "test_consensus"

        for _ in range(10):
            action, regime, reason = processor._apply_temporal_governance(
                session_id=session_id,
                classification="consensus",
                instantaneous_action="allow",
            )
            assert action == "allow"
            assert regime is None
            assert reason is None

    def test_fluctuating_states_dont_sustain(self, monkeypatch):
        """Alternating states don't trigger sustained detection."""
        monkeypatch.setenv("NOVA_ENABLE_BIAS_DETECTION", "1")
        monkeypatch.setenv("NOVA_ENABLE_USM_TEMPORAL", "1")
        monkeypatch.setenv("NOVA_ENABLE_TEMPORAL_GOVERNANCE", "1")
        processor = DeltaThreshProcessor()

        session_id = "test_fluctuating"
        states = ["extractive", "extractive", "neutral", "extractive", "extractive", "neutral"]

        for state in states:
            action, regime, reason = processor._apply_temporal_governance(
                session_id=session_id,
                classification=state,
                instantaneous_action="allow",
            )
            # Should never escalate (not 5 consecutive extractive)
            assert action == "allow"
            assert regime is None
            assert reason is None

    def test_history_limited_to_10_turns(self, monkeypatch):
        """Classification history keeps only last 10 turns."""
        monkeypatch.setenv("NOVA_ENABLE_BIAS_DETECTION", "1")
        monkeypatch.setenv("NOVA_ENABLE_USM_TEMPORAL", "1")
        monkeypatch.setenv("NOVA_ENABLE_TEMPORAL_GOVERNANCE", "1")
        processor = DeltaThreshProcessor()

        session_id = "test_history_limit"

        # Add 15 turns
        for _ in range(15):
            processor._apply_temporal_governance(
                session_id=session_id,
                classification="neutral",
                instantaneous_action="allow",
            )

        # History should be capped at 10
        assert len(processor._classification_history[session_id]) == 10

    def test_warming_up_ignored(self, monkeypatch):
        """warming_up classification doesn't contribute to sustained patterns."""
        monkeypatch.setenv("NOVA_ENABLE_BIAS_DETECTION", "1")
        monkeypatch.setenv("NOVA_ENABLE_USM_TEMPORAL", "1")
        monkeypatch.setenv("NOVA_ENABLE_TEMPORAL_GOVERNANCE", "1")
        processor = DeltaThreshProcessor()

        session_id = "test_warming_up"

        # 3 warming_up + 5 extractive = should trigger on turn 8
        for _ in range(3):
            action, regime, _ = processor._apply_temporal_governance(
                session_id=session_id,
                classification="warming_up",
                instantaneous_action="allow",
            )
            assert action == "allow"
            assert regime is None

        # Now 5 extractive turns
        for turn in range(5):
            action, regime, reason = processor._apply_temporal_governance(
                session_id=session_id,
                classification="extractive",
                instantaneous_action="allow",
            )
            if turn < 4:
                assert action == "allow"
            else:
                assert action == "quarantine"
                assert regime == "heightened"
