"""Comprehensive test suite for Slot 3 escalation functionality."""
import pytest
import time
from unittest.mock import Mock, patch

from slots.slot03_emotional_matrix.escalation import (
    EmotionalEscalationManager, ThreatLevel, EscalationEvent
)


class TestEmotionalEscalationManager:
    """Test suite for EmotionalEscalationManager."""

    def setup_method(self):
        """Set up test fixtures."""
        self.manager = EmotionalEscalationManager()

    def test_threat_classification(self):
        """Test threat level classification logic."""
        # Critical threat
        critical_analysis = {
            'score': -0.9,
            'emotional_tone': 'anger',
            'confidence': 0.9
        }
        assert self.manager.classify_threat(critical_analysis) == ThreatLevel.CRITICAL

        # High threat
        high_analysis = {
            'score': -0.7,
            'emotional_tone': 'fear',
            'confidence': 0.8
        }
        assert self.manager.classify_threat(high_analysis) == ThreatLevel.HIGH

        # Medium threat
        medium_analysis = {
            'score': -0.5,
            'emotional_tone': 'sadness',
            'confidence': 0.6
        }
        assert self.manager.classify_threat(medium_analysis) == ThreatLevel.MEDIUM

        # Low threat
        low_analysis = {
            'score': -0.3,
            'emotional_tone': 'neutral',
            'confidence': 0.4
        }
        assert self.manager.classify_threat(low_analysis) == ThreatLevel.LOW

    def test_escalation_process(self):
        """Test full escalation process."""
        content = "I hate everything about this system!"
        analysis = {
            'score': -0.8,
            'emotional_tone': 'anger',
            'confidence': 0.85
        }

        event = self.manager.escalate(content, analysis)

        assert isinstance(event, EscalationEvent)
        assert event.threat_level == ThreatLevel.HIGH
        assert event.content == content
        assert event.emotional_analysis == analysis
        assert len(event.suggested_actions) > 0
        assert event.escalation_reason

    def test_handler_registration_and_execution(self):
        """Test escalation handler registration and execution."""
        handler_calls = []
        
        def test_handler(event):
            handler_calls.append(event)

        self.manager.register_handler(ThreatLevel.HIGH, test_handler)

        analysis = {
            'score': -0.7,
            'emotional_tone': 'anger',
            'confidence': 0.8
        }

        event = self.manager.escalate("test content", analysis)

        assert len(handler_calls) == 1
        assert handler_calls[0] == event

    def test_inter_slot_routing(self):
        """Test routing to other slots via adapter registry."""
        mock_slot1 = Mock()
        mock_slot4 = Mock()
        
        adapter_registry = {
            'slot01_truth': mock_slot1,
            'slot04_wisdom': mock_slot4
        }
        
        manager = EmotionalEscalationManager(adapter_registry)

        critical_analysis = {
            'score': -0.9,
            'emotional_tone': 'violence',
            'confidence': 0.95
        }

        event = manager.escalate("threatening content", critical_analysis)

        # Critical threats should route to both slot01_truth and slot04_wisdom
        mock_slot1.receive_escalation.assert_called_once_with(event)
        mock_slot4.receive_escalation.assert_called_once_with(event)

    def test_escalation_summary(self):
        """Test escalation summary generation."""
        # Generate some escalations
        analyses = [
            {'score': -0.9, 'emotional_tone': 'anger', 'confidence': 0.9},
            {'score': -0.6, 'emotional_tone': 'fear', 'confidence': 0.7},
            {'score': -0.3, 'emotional_tone': 'sadness', 'confidence': 0.5}
        ]

        for i, analysis in enumerate(analyses):
            self.manager.escalate(f"content {i}", analysis)

        summary = self.manager.get_escalation_summary()

        assert summary['total_escalations'] == 3
        assert summary['threat_level_distribution']['critical'] >= 1
        assert summary['threat_level_distribution']['high'] >= 1
        assert summary['most_recent'] is not None

    def test_handler_error_handling(self):
        """Test escalation continues even if handlers fail."""
        def failing_handler(event):
            raise Exception("Handler failed")

        self.manager.register_handler(ThreatLevel.MEDIUM, failing_handler)

        analysis = {
            'score': -0.5,
            'emotional_tone': 'anger',
            'confidence': 0.6
        }

        # Should not raise exception
        event = self.manager.escalate("test", analysis)
        assert isinstance(event, EscalationEvent)

    def test_escalation_reasons(self):
        """Test escalation reason generation."""
        analysis = {
            'score': -0.8,
            'emotional_tone': 'anger',
            'confidence': 0.85
        }

        event = self.manager.escalate("test content", analysis)

        assert "anger" in event.escalation_reason.lower()
        assert "-0.8" in event.escalation_reason or "-0.80" in event.escalation_reason
        assert "0.85" in event.escalation_reason

    def test_suggested_actions_vary_by_threat_level(self):
        """Test that suggested actions vary appropriately by threat level."""
        analyses = {
            ThreatLevel.CRITICAL: {'score': -0.9, 'emotional_tone': 'violence', 'confidence': 0.9},
            ThreatLevel.HIGH: {'score': -0.7, 'emotional_tone': 'anger', 'confidence': 0.8},
            ThreatLevel.MEDIUM: {'score': -0.5, 'emotional_tone': 'fear', 'confidence': 0.6},
            ThreatLevel.LOW: {'score': -0.3, 'emotional_tone': 'sadness', 'confidence': 0.4}
        }

        events = {}
        for level, analysis in analyses.items():
            event = self.manager.escalate(f"content for {level.value}", analysis)
            events[level] = event

        # Critical should have most actions, low should have least
        assert len(events[ThreatLevel.CRITICAL].suggested_actions) > len(events[ThreatLevel.LOW].suggested_actions)
        
        # Check for specific critical actions
        critical_actions = " ".join(events[ThreatLevel.CRITICAL].suggested_actions).lower()
        assert "quarantine" in critical_actions or "alert" in critical_actions


class TestEscalationEvent:
    """Test suite for EscalationEvent dataclass."""

    def test_escalation_event_creation(self):
        """Test EscalationEvent creation and defaults."""
        event = EscalationEvent(
            threat_level=ThreatLevel.HIGH,
            content="test content",
            emotional_analysis={'score': -0.7},
            timestamp=time.time()
        )

        assert event.threat_level == ThreatLevel.HIGH
        assert event.content == "test content"
        assert event.source_slot == "slot03_emotional"
        assert isinstance(event.suggested_actions, list)

    def test_escalation_event_with_custom_values(self):
        """Test EscalationEvent with all custom values."""
        custom_actions = ["action1", "action2"]
        event = EscalationEvent(
            threat_level=ThreatLevel.CRITICAL,
            content="critical content",
            emotional_analysis={'score': -0.9},
            timestamp=time.time(),
            source_slot="custom_slot",
            escalation_reason="Custom reason",
            suggested_actions=custom_actions
        )

        assert event.source_slot == "custom_slot"
        assert event.escalation_reason == "Custom reason"
        assert event.suggested_actions == custom_actions


class TestThreatLevel:
    """Test suite for ThreatLevel enum."""

    def test_threat_level_values(self):
        """Test ThreatLevel enum values."""
        assert ThreatLevel.LOW.value == "low"
        assert ThreatLevel.MEDIUM.value == "medium"
        assert ThreatLevel.HIGH.value == "high"
        assert ThreatLevel.CRITICAL.value == "critical"

    def test_threat_level_comparison(self):
        """Test ThreatLevel enum can be compared."""
        levels = [ThreatLevel.LOW, ThreatLevel.MEDIUM, ThreatLevel.HIGH, ThreatLevel.CRITICAL]
        
        # Test that we can use levels in sets, lists, etc.
        level_set = set(levels)
        assert len(level_set) == 4
        
        # Test equality
        assert ThreatLevel.HIGH == ThreatLevel.HIGH
        assert ThreatLevel.HIGH != ThreatLevel.LOW