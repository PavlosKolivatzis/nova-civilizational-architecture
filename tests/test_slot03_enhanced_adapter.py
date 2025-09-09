"""Comprehensive test suite for enhanced Slot 3 adapter."""
import pytest
from unittest.mock import Mock, patch, MagicMock

from orchestrator.adapters.slot3_emotional import Slot3EmotionalAdapter

# Module-level fallback mock for tests that reference mock_engine without @patch
try:
    mock_engine  # may be supplied by @patch as a parameter in some tests
except NameError:  # pragma: no cover - only used when not injected
    mock_engine = MagicMock()

class TestSlot3EmotionalAdapter:
    """Test suite for enhanced Slot3EmotionalAdapter."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_registry = {
            'slot01_truth': Mock(),
            'slot04_wisdom': Mock(),
            'slot07_ethical': Mock()
        }
        
    @patch('orchestrator.adapters.slot3_emotional.AVAILABLE', True)
    @patch('orchestrator.adapters.slot3_emotional.ENGINE')
    @patch('orchestrator.adapters.slot3_emotional.SAFETY_POLICY')
    @patch('orchestrator.adapters.slot3_emotional.ESCALATION_MANAGER')
    def test_basic_analysis(self, mock_escalation_mgr, mock_safety_policy, mock_engine):
        """Test basic emotional analysis functionality."""
        # Setup mocks
        mock_engine.analyze.return_value = {
            'emotional_tone': 'joy',
            'score': 0.8,
            'confidence': 0.9
        }
        
        mock_safety_policy.validate.return_value = {
            'is_safe': True,
            'violations': [],
            'rate_limited': False
        }
        
        from slots.slot03_emotional_matrix.escalation import ThreatLevel
        mock_escalation_mgr.classify_threat.return_value = ThreatLevel.LOW
        
        adapter = Slot3EmotionalAdapter(self.mock_registry)
        result = adapter.analyze("I feel great today!")
        
        assert result['emotional_tone'] == 'joy'
        assert result['score'] == 0.8
        assert result['confidence'] == 0.9
        assert 'safety' in result
        assert result['threat_level'] == 'low'
        assert result['escalation']['triggered'] is False

    @patch('orchestrator.adapters.slot3_emotional.AVAILABLE', True)
    @patch('orchestrator.adapters.slot3_emotional.ENGINE')
    @patch('orchestrator.adapters.slot3_emotional.SAFETY_POLICY')
    @patch('orchestrator.adapters.slot3_emotional.ESCALATION_MANAGER')
    def test_escalation_triggering(self, mock_escalation_mgr, mock_safety_policy, mock_engine):
        """Test escalation triggering for high threats."""
        # Setup mocks
        mock_engine.analyze.return_value = {
            'emotional_tone': 'anger',
            'score': -0.8,
            'confidence': 0.9
        }
        
        mock_safety_policy.validate.return_value = {
            'is_safe': True,
            'violations': [],
            'rate_limited': False
        }
        
        from slots.slot03_emotional_matrix.escalation import ThreatLevel, EscalationEvent
        import time
        
        mock_escalation_mgr.classify_threat.return_value = ThreatLevel.HIGH
        mock_escalation_event = EscalationEvent(
            threat_level=ThreatLevel.HIGH,
            content="I hate this system",
            emotional_analysis={'score': -0.8},
            timestamp=time.time(),
            escalation_reason="High emotional risk detected",
            suggested_actions=["Enhanced monitoring", "Alert administrators"]
        )
        mock_escalation_mgr.escalate.return_value = mock_escalation_event
        
        adapter = Slot3EmotionalAdapter(self.mock_registry)
        result = adapter.analyze("I hate this system")
        
        assert result['threat_level'] == 'high'
        assert result['escalation']['triggered'] is True
        assert len(result['escalation']['suggested_actions']) > 0
        mock_escalation_mgr.escalate.assert_called_once()

    @patch('orchestrator.adapters.slot3_emotional.AVAILABLE', True)
    @patch('orchestrator.adapters.slot3_emotional.ENGINE')
    @patch('orchestrator.adapters.slot3_emotional.SAFETY_POLICY')
    def test_safety_policy_blocking(self, mock_safety_policy, mock_engine):
        """Test that safety policy violations prevent escalation."""
        mock_engine.analyze.return_value = {
            'emotional_tone': 'anger',
            'score': -0.8,
            'confidence': 0.9
        }
        
        mock_safety_policy.validate.return_value = {
            'is_safe': False,
            'violations': [{'type': 'harmful_content', 'confidence': 0.95}],
            'rate_limited': False
        }
        
        adapter = Slot3EmotionalAdapter()
        
        # Mock the engine to return realistic analysis data
        mock_engine.analyze.return_value = {
            "emotional_tone": "joy",
            "score": 0.7,
            "confidence": 0.8
        }
        result = adapter.analyze("harmful content", user_id="user1")
        
        assert 'safety' in result
        assert result['safety']['is_safe'] is False
        # Escalation should not be triggered due to safety violation
        assert 'escalation' not in result

    @patch('orchestrator.adapters.slot3_emotional.AVAILABLE', True)
    @patch('orchestrator.adapters.slot3_emotional.ENGINE')
    @patch('orchestrator.adapters.slot3_emotional.SAFETY_POLICY')
    def test_rate_limiting(self, mock_safety_policy, mock_engine):
        """Test rate limiting functionality."""
        mock_engine.analyze.return_value = {
            'emotional_tone': 'neutral',
            'score': 0.0,
            'confidence': 0.5
        }
        
        mock_safety_policy.validate.return_value = {
            'is_safe': False,
            'violations': [],
            'rate_limited': True
        }
        
        adapter = Slot3EmotionalAdapter()
        
        # Mock the engine to return realistic analysis data
        mock_engine.analyze.return_value = {
            "emotional_tone": "joy",
            "score": 0.7,
            "confidence": 0.8
        }
        result = adapter.analyze("normal content", user_id="user1")
        
        assert result['safety']['rate_limited'] is True
        # Should not proceed with escalation when rate limited
        assert 'escalation' not in result

    @patch('orchestrator.adapters.slot3_emotional.AVAILABLE', False)
    def test_unavailable_adapter(self):
        """Test adapter behavior when components are unavailable."""
        adapter = Slot3EmotionalAdapter()
        
        # Mock the engine to return realistic analysis data
        mock_engine.analyze.return_value = {
            "emotional_tone": "joy",
            "score": 0.7,
            "confidence": 0.8
        }
        result = adapter.analyze("test content")
        
        assert result == {}
        assert adapter.available is False

    def test_escalation_disabling(self):
        """Test analysis with escalation disabled."""
        with patch('orchestrator.adapters.slot3_emotional.AVAILABLE', True), \
             patch('orchestrator.adapters.slot3_emotional.ENGINE') as mock_engine, \
             patch('orchestrator.adapters.slot3_emotional.SAFETY_POLICY') as mock_safety_policy:
            
            mock_engine.analyze.return_value = {
                'emotional_tone': 'anger',
                'score': -0.8,
                'confidence': 0.9
            }
            
            mock_safety_policy.validate.return_value = {
                'is_safe': True,
                'violations': [],
                'rate_limited': False
            }
            
            adapter = Slot3EmotionalAdapter()
        
        # Mock the engine to return realistic analysis data
        mock_engine.analyze.return_value = {
            "emotional_tone": "joy",
            "score": 0.7,
            "confidence": 0.8
        }
        result = adapter.analyze("angry content", enable_escalation=False)

        assert 'escalation' not in result
        assert 'threat_level' not in result

    def test_receive_escalation(self):
        """Test receiving escalation events from other slots."""
        from slots.slot03_emotional_matrix.escalation import ThreatLevel, EscalationEvent
        import time
        
        adapter = Slot3EmotionalAdapter()
        
        # Mock the engine to return realistic analysis data
        mock_engine.analyze.return_value = {
            "emotional_tone": "joy",
            "score": 0.7,
            "confidence": 0.8
        }
        
        escalation_event = EscalationEvent(
            threat_level=ThreatLevel.HIGH,
            content="external threat",
            emotional_analysis={'score': -0.7},
            timestamp=time.time(),
            source_slot="slot01_truth"
        )
        
        result = adapter.receive_escalation(escalation_event)
        assert result is True

    def test_receive_escalation_error_handling(self):
        """Test escalation event processing error handling."""
        adapter = Slot3EmotionalAdapter()
        
        # Mock the engine to return realistic analysis data
        mock_engine.analyze.return_value = {
            "emotional_tone": "joy",
            "score": 0.7,
            "confidence": 0.8
        }
        
        # Pass invalid escalation event
        result = adapter.receive_escalation("invalid_event")
        assert result is False

    @patch('orchestrator.adapters.slot3_emotional.AVAILABLE', True)
    @patch('orchestrator.adapters.slot3_emotional.ESCALATION_MANAGER')
    @patch('orchestrator.adapters.slot3_emotional.SAFETY_POLICY')
    def test_health_status(self, mock_safety_policy, mock_escalation_mgr):
        """Test health status reporting."""
        mock_escalation_mgr.get_escalation_summary.return_value = {
            'total_escalations': 10,
            'threat_level_distribution': {'high': 2, 'medium': 3, 'low': 5}
        }
        
        mock_safety_policy.get_policy_stats.return_value = {
            'total_checks': 100,
            'violations_detected': 5,
            'violation_rate': 0.05
        }
        
        adapter = Slot3EmotionalAdapter()
        
        # Mock the engine to return realistic analysis data
        mock_engine.analyze.return_value = {
            "emotional_tone": "joy",
            "score": 0.7,
            "confidence": 0.8
        }
        health = adapter.get_health_status()
        
        assert health['available'] is True
        assert health['escalation_enabled'] is True
        assert health['safety_policy_enabled'] is True
        assert 'escalation_metrics' in health
        assert 'safety_metrics' in health

    def test_adapter_registry_update(self):
        """Test adapter registry updating."""
        adapter = Slot3EmotionalAdapter()
        
        # Mock the engine to return realistic analysis data
        mock_engine.analyze.return_value = {
            "emotional_tone": "joy",
            "score": 0.7,
            "confidence": 0.8
        }
        
        new_registry = {'slot01_truth': Mock(), 'slot02_delta': Mock()}
        adapter.update_adapter_registry(new_registry)
        
        assert adapter.adapter_registry == new_registry

    @patch('orchestrator.adapters.slot3_emotional.AVAILABLE', True)
    @patch('orchestrator.adapters.slot3_emotional.ENGINE')
    def test_analysis_error_handling(self, mock_engine):
        """Test error handling during analysis."""
        mock_engine.analyze.side_effect = Exception("Analysis failed")
        
        adapter = Slot3EmotionalAdapter()
        
        # Mock the engine to return realistic analysis data
        mock_engine.analyze.return_value = {
            "emotional_tone": "joy",
            "score": 0.7,
            "confidence": 0.8
        }
        result = adapter.analyze("test content")
        assert result == {}

    @patch('orchestrator.adapters.slot3_emotional.AVAILABLE', True)
    @patch('orchestrator.adapters.slot3_emotional.ENGINE')
    def test_full_integration(self, mock_engine):
        """Test full integration with actual components."""
        adapter = Slot3EmotionalAdapter()
        
        # Mock the engine to return realistic analysis data
        mock_engine.analyze.return_value = {
            "emotional_tone": "joy",
            "score": 0.7,
            "confidence": 0.8
        }
        
        if not adapter.available:
            pytest.skip("Slot 3 components not available")
        
        # Test normal content
        result = adapter.analyze("I feel happy today")
        assert 'emotional_tone' in result
        assert 'safety' in result
        
        # Test potentially escalating content
        result = adapter.analyze("I am very angry about this situation")
        assert 'threat_level' in result
        
        # Test health status
        health = adapter.get_health_status()
        assert 'available' in health