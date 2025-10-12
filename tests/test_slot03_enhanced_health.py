"""Test suite for enhanced Slot 3 health monitoring."""
import pytest
from unittest.mock import Mock, patch

from nova.slots.slot03_emotional_matrix.health import health, get_detailed_metrics


class TestSlot3HealthMonitoring:
    """Test suite for Slot 3 health monitoring functionality."""

    @patch('nova.slots.slot03_emotional_matrix.health.emotional_matrix_engine.EmotionalMatrixEngine')
    def test_basic_health_check_success(self, mock_engine_class):
        """Test successful basic health check."""
        # Mock engine instance and analysis result
        mock_engine = Mock()
        mock_engine.analyze.return_value = {
            'emotional_tone': 'joy',
            'score': 0.8,
            'confidence': 0.9
        }
        mock_engine_class.return_value = mock_engine
        
        # Mock all the enhanced components to be available
        with patch('nova.slots.slot03_emotional_matrix.escalation.EmotionalEscalationManager') as mock_escalation, \
             patch('nova.slots.slot03_emotional_matrix.advanced_policy.AdvancedSafetyPolicy') as mock_safety, \
             patch('nova.slots.slot03_emotional_matrix.enhanced_engine.EnhancedEmotionalMatrixEngine') as mock_enhanced:
            
            # Setup escalation manager mock
            mock_escalation_instance = Mock()
            from nova.slots.slot03_emotional_matrix.escalation import ThreatLevel
            mock_escalation_instance.classify_threat.return_value = ThreatLevel.LOW
            mock_escalation.return_value = mock_escalation_instance
            
            # Setup safety policy mock
            mock_safety_instance = Mock()
            mock_safety_instance.validate.return_value = {
                'is_safe': True,
                'violations': []
            }
            mock_safety.return_value = mock_safety_instance
            
            # Setup enhanced engine mock
            mock_enhanced_instance = Mock()
            mock_enhanced_instance.analyze.return_value = {'enhanced': True}
            mock_enhanced_instance.get_performance_metrics.return_value = {
                'total_analyses': 100,
                'threat_detections': 5
            }
            mock_enhanced.return_value = mock_enhanced_instance
            
            result = health()
            
            assert result['self_check'] == 'ok'
            assert result['engine_status'] == 'operational'
            assert result['basic_analysis'] == 'functional'
            assert result['escalation_status'] == 'operational'
            assert result['safety_policy_status'] == 'operational'
            assert result['enhanced_engine_status'] == 'operational'
            assert result['overall_status'] == 'fully_operational'
            assert result['maturity_level'] == '4/4_processual'

    @patch('nova.slots.slot03_emotional_matrix.health.emotional_matrix_engine.EmotionalMatrixEngine')
    def test_health_check_with_failures(self, mock_engine_class):
        """Test health check with component failures."""
        # Mock engine instance
        mock_engine = Mock()
        mock_engine.analyze.return_value = {
            'emotional_tone': 'neutral',
            'score': 0.0,
            'confidence': 0.5
        }
        mock_engine_class.return_value = mock_engine
        
        # Mock escalation manager to fail
        with patch('nova.slots.slot03_emotional_matrix.escalation.EmotionalEscalationManager') as mock_escalation, \
             patch('nova.slots.slot03_emotional_matrix.advanced_policy.AdvancedSafetyPolicy') as mock_safety, \
             patch('nova.slots.slot03_emotional_matrix.enhanced_engine.EnhancedEmotionalMatrixEngine') as mock_enhanced:
            
            # Make escalation manager fail
            mock_escalation.side_effect = Exception("Escalation manager failed")
            
            # Make safety policy work
            mock_safety_instance = Mock()
            mock_safety_instance.validate.return_value = {'is_safe': True, 'violations': []}
            mock_safety.return_value = mock_safety_instance
            
            # Make enhanced engine fail
            mock_enhanced.side_effect = Exception("Enhanced engine failed")
            
            result = health()
            
            assert result['self_check'] == 'ok'
            assert result['basic_analysis'] == 'functional'
            assert result['escalation_status'] == 'degraded'
            assert result['safety_policy_status'] == 'operational'
            assert result['enhanced_engine_status'] == 'degraded'
            assert result['overall_status'] == 'partially_operational'
            assert result['maturity_level'] == '2/4_relational'

    @patch('nova.slots.slot03_emotional_matrix.health.emotional_matrix_engine.EmotionalMatrixEngine')
    def test_health_check_critical_failure(self, mock_engine_class):
        """Test health check with critical engine failure."""
        # Make the base engine fail
        mock_engine_class.side_effect = Exception("Critical engine failure")
        
        result = health()
        
        assert result['self_check'] == 'error'
        assert result['engine_status'] == 'failed'
        assert result['overall_status'] == 'critical_failure'
        assert result['maturity_level'] == '0/4_missing'
        assert 'error' in result
        assert 'timestamp' in result

    @patch('nova.slots.slot03_emotional_matrix.health.emotional_matrix_engine.EmotionalMatrixEngine')
    def test_health_check_basic_analysis_failure(self, mock_engine_class):
        """Test health check when basic analysis fails."""
        # Mock engine that returns invalid results
        mock_engine = Mock()
        mock_engine.analyze.return_value = None
        mock_engine_class.return_value = mock_engine
        
        result = health()
        
        assert result['basic_analysis'] == 'degraded'

    def test_health_check_includes_timestamp(self):
        """Test that health check includes timestamp."""
        with patch('nova.slots.slot03_emotional_matrix.health.emotional_matrix_engine.EmotionalMatrixEngine'):
            result = health()
            assert 'timestamp' in result
            assert isinstance(result['timestamp'], float)

    def test_health_check_sample_analysis_content(self):
        """Test that health check includes sample analysis results."""
        with patch('nova.slots.slot03_emotional_matrix.health.emotional_matrix_engine.EmotionalMatrixEngine') as mock_engine_class:
            mock_engine = Mock()
            mock_engine.analyze.return_value = {
                'emotional_tone': 'joy',
                'score': 0.8,
                'confidence': 0.9
            }
            mock_engine_class.return_value = mock_engine
            
            result = health()
            
            assert 'sample_analysis' in result
            assert result['sample_analysis']['tone'] == 'joy'
            assert result['sample_analysis']['score'] == 0.8
            assert result['sample_analysis']['confidence'] == 0.9


class TestDetailedMetrics:
    """Test suite for detailed metrics functionality."""

    def test_get_detailed_metrics_success(self):
        """Test successful detailed metrics collection."""
        with patch('nova.slots.slot03_emotional_matrix.escalation.EmotionalEscalationManager') as mock_escalation, \
             patch('nova.slots.slot03_emotional_matrix.advanced_policy.AdvancedSafetyPolicy') as mock_safety, \
             patch('nova.slots.slot03_emotional_matrix.enhanced_engine.EnhancedEmotionalMatrixEngine') as mock_enhanced:
            
            # Setup mocks
            mock_escalation_instance = Mock()
            mock_escalation_instance.get_escalation_summary.return_value = {
                'total_escalations': 50,
                'threat_level_distribution': {'high': 5, 'medium': 10, 'low': 35}
            }
            mock_escalation.return_value = mock_escalation_instance
            
            mock_safety_instance = Mock()
            mock_safety_instance.get_policy_stats.return_value = {
                'total_checks': 1000,
                'violations_detected': 25,
                'violation_rate': 0.025
            }
            mock_safety.return_value = mock_safety_instance
            
            mock_enhanced_instance = Mock()
            mock_enhanced_instance.get_performance_metrics.return_value = {
                'total_analyses': 1000,
                'threat_detections': 50,
                'threat_detection_rate': 0.05
            }
            mock_enhanced.return_value = mock_enhanced_instance
            
            result = get_detailed_metrics()
            
            assert 'timestamp' in result
            assert 'component_metrics' in result
            assert 'escalation' in result['component_metrics']
            assert 'safety_policy' in result['component_metrics']
            assert 'enhanced_engine' in result['component_metrics']
            
            # Check escalation metrics
            escalation_metrics = result['component_metrics']['escalation']
            assert escalation_metrics['total_escalations'] == 50
            assert 'threat_level_distribution' in escalation_metrics
            
            # Check safety policy metrics
            safety_metrics = result['component_metrics']['safety_policy']
            assert safety_metrics['total_checks'] == 1000
            assert safety_metrics['violations_detected'] == 25
            
            # Check enhanced engine metrics
            enhanced_metrics = result['component_metrics']['enhanced_engine']
            assert enhanced_metrics['total_analyses'] == 1000
            assert enhanced_metrics['threat_detections'] == 50

    def test_get_detailed_metrics_with_failures(self):
        """Test detailed metrics collection with component failures."""
        with patch('nova.slots.slot03_emotional_matrix.escalation.EmotionalEscalationManager') as mock_escalation, \
             patch('nova.slots.slot03_emotional_matrix.advanced_policy.AdvancedSafetyPolicy') as mock_safety, \
             patch('nova.slots.slot03_emotional_matrix.enhanced_engine.EnhancedEmotionalMatrixEngine') as mock_enhanced:
            
            # Make escalation manager fail
            mock_escalation.side_effect = Exception("Escalation failed")
            
            # Make safety policy work
            mock_safety_instance = Mock()
            mock_safety_instance.get_policy_stats.return_value = {'total_checks': 100}
            mock_safety.return_value = mock_safety_instance
            
            # Make enhanced engine fail
            mock_enhanced.side_effect = Exception("Enhanced engine failed")
            
            result = get_detailed_metrics()
            
            assert result['component_metrics']['escalation']['status'] == 'unavailable'
            assert result['component_metrics']['safety_policy']['total_checks'] == 100
            assert result['component_metrics']['enhanced_engine']['status'] == 'unavailable'

    def test_get_detailed_metrics_critical_failure(self):
        """Test detailed metrics with critical failure."""
        with patch('nova.slots.slot03_emotional_matrix.escalation.EmotionalEscalationManager') as mock_escalation:
            # Make the entire function fail
            mock_escalation.side_effect = Exception("Critical failure")
            
            result = get_detailed_metrics()
            
            # Should return normally even with component failures
            assert result["component_metrics"]["escalation"]["status"] == "unavailable"

    def test_detailed_metrics_includes_timestamp(self):
        """Test that detailed metrics includes timestamp."""
        result = get_detailed_metrics()
        assert 'timestamp' in result
        assert isinstance(result['timestamp'], float)


class TestHealthIntegration:
    """Integration tests for health monitoring."""

    @pytest.mark.skipif(
        True,  # Skip by default
        reason="Integration test - requires actual slot components"
    )
    def test_real_health_check(self):
        """Test health check with real components if available."""
        try:
            result = health()
            
            # Basic checks that should always pass
            assert 'self_check' in result
            assert 'engine_status' in result
            assert 'timestamp' in result
            assert 'overall_status' in result
            assert 'maturity_level' in result
            
            # If components are available, check their status
            if result.get('escalation_status') == 'operational':
                assert 'escalation_test' in result
            
            if result.get('safety_policy_status') == 'operational':
                assert 'safety_test' in result
                
            if result.get('enhanced_engine_status') == 'operational':
                assert 'performance_metrics' in result
                
        except ImportError:
            pytest.skip("Real components not available for integration test")

    @pytest.mark.skipif(
        True,  # Skip by default
        reason="Integration test - requires actual slot components"
    )
    def test_real_detailed_metrics(self):
        """Test detailed metrics with real components if available."""
        try:
            result = get_detailed_metrics()
            
            assert 'timestamp' in result
            assert 'component_metrics' in result
            
            # Check that each component either has metrics or shows unavailable
            for component in ['escalation', 'safety_policy', 'enhanced_engine']:
                assert component in result['component_metrics']
                component_data = result['component_metrics'][component]
                assert isinstance(component_data, dict)
                
        except ImportError:
            pytest.skip("Real components not available for integration test")