"""Validation tests for Slot 5 Processual-level capabilities.

These tests validate the advanced adaptive processing capabilities required
for 4.0 Processual maturity level in the constellation navigation system.
"""

import pytest
import time
from unittest.mock import MagicMock

from slots.slot05_constellation.enhanced_constellation_engine import EnhancedConstellationEngine
from slots.slot05_constellation.adaptive_processor import AdaptiveProcessor
from orchestrator.adapters.enhanced_slot5_constellation import EnhancedSlot5ConstellationAdapter


class TestAdaptiveProcessor:
    """Test suite for adaptive processing capabilities."""

    @pytest.fixture
    def processor(self):
        """Create adaptive processor for testing."""
        mock_semantic_mirror = MagicMock()
        mock_semantic_mirror.publish = MagicMock(return_value=True)
        return AdaptiveProcessor(mock_semantic_mirror)

    def test_adaptive_threshold_initialization(self, processor):
        """Test that adaptive processor initializes with correct thresholds."""
        thresholds = processor.get_current_thresholds()

        assert 'similarity' in thresholds
        assert 'stability_window' in thresholds
        assert 'link_strength' in thresholds
        assert 0.1 <= thresholds['similarity'] <= 0.8
        assert 3 <= thresholds['stability_window'] <= 50
        assert 0.05 <= thresholds['link_strength'] <= 0.6

    def test_context_analysis(self, processor):
        """Test context analysis capabilities."""
        # Test sparse context
        sparse_context = {'item_count': 3, 'avg_complexity': 0.2}
        signature = processor._analyze_context(sparse_context)
        assert 'sparse' in signature
        assert 'simple' in signature

        # Test dense complex context
        dense_context = {'item_count': 25, 'avg_complexity': 0.8}
        signature = processor._analyze_context(dense_context)
        assert 'dense' in signature
        assert 'complex' in signature

    def test_threshold_adaptation(self, processor):
        """Test dynamic threshold adaptation."""
        context = {
            'item_count': 10,
            'avg_complexity': 0.5,
            'stability_requirement': 'high'
        }

        performance = {
            'stability_score': 0.3,  # Poor performance
            'connectivity': 0.4,
            'processing_time': 0.1
        }

        # First adaptation
        initial_thresholds = processor.get_current_thresholds()
        adapted_thresholds = processor.adapt_thresholds(context, performance)

        # Should adapt thresholds based on poor performance
        assert adapted_thresholds != initial_thresholds

        # Test learning from multiple adaptations
        for i in range(5):
            better_performance = {
                'stability_score': 0.7 + (i * 0.05),
                'connectivity': 0.6,
                'processing_time': 0.08
            }
            adapted_thresholds = processor.adapt_thresholds(context, better_performance)

        # Should show adaptation metrics
        metrics = processor.get_adaptation_metrics()
        assert metrics['total_adaptations'] >= 6
        assert metrics['contexts_learned'] >= 1

    def test_learning_from_history(self, processor):
        """Test learning from historical performance data."""
        context = {'item_count': 8, 'avg_complexity': 0.6}

        # Build history with consistent pattern
        for i in range(10):
            performance = {
                'stability_score': 0.5 + (i * 0.03),  # Improving performance
                'connectivity': 0.6,
                'processing_time': 0.1 - (i * 0.005)  # Faster over time
            }
            processor.adapt_thresholds(context, performance)

        # Should have learned from history
        metrics = processor.get_adaptation_metrics()
        assert metrics['total_adaptations'] == 10
        assert len(processor._context_patterns) >= 1

    def test_bounds_enforcement(self, processor):
        """Test that threshold adaptations stay within bounds."""
        context = {'item_count': 50, 'avg_complexity': 0.9}

        # Extreme performance scenarios
        extreme_performance = {
            'stability_score': 0.0,  # Terrible performance
            'connectivity': 0.0,
            'processing_time': 5.0
        }

        # Multiple extreme adaptations
        for _ in range(20):
            thresholds = processor.adapt_thresholds(context, extreme_performance)

            # Verify bounds
            assert 0.1 <= thresholds['similarity'] <= 0.8
            assert 0.05 <= thresholds['link_strength'] <= 0.6
            assert 3 <= thresholds['stability_window'] <= 50


class TestEnhancedConstellationEngine:
    """Test suite for enhanced constellation engine."""

    @pytest.fixture
    def engine(self):
        """Create enhanced constellation engine for testing."""
        mock_semantic_mirror = MagicMock()
        mock_semantic_mirror.publish = MagicMock(return_value=True)
        return EnhancedConstellationEngine(mock_semantic_mirror)

    def test_enhanced_mapping_with_context(self, engine):
        """Test enhanced mapping with contextual processing."""
        items = [
            "process optimization algorithm",
            "algorithm performance metrics",
            "metrics data analysis",
            "analysis result interpretation",
            "interpretation error handling"
        ]

        context = {
            'stability_requirement': 'high',
            'time_constraint': 'normal'
        }

        result = engine.map(items, context)

        # Should contain standard constellation elements
        assert 'constellation' in result
        assert 'links' in result
        assert 'stability' in result

        # Should contain adaptive enhancements
        assert 'adaptive' in result
        assert 'thresholds_used' in result['adaptive']
        assert 'context' in result['adaptive']
        assert 'performance' in result['adaptive']
        assert 'processing_time' in result['adaptive']

    def test_adaptive_threshold_application(self, engine):
        """Test that adaptive thresholds are properly applied."""
        items = ["test item one", "test item two", "related test item"]

        # Get initial thresholds
        initial_thresholds = engine.adaptive_processor.get_current_thresholds()

        # Map with context that should trigger adaptation
        context = {'item_count': 3, 'avg_complexity': 0.8}
        result1 = engine.map(items, context)

        # Map again with different context
        different_context = {'item_count': 3, 'avg_complexity': 0.2}
        result2 = engine.map(items, different_context)

        # Should have different adaptive configurations
        assert result1['adaptive']['thresholds_used'] != result2['adaptive']['thresholds_used']

    def test_performance_tracking(self, engine):
        """Test performance metrics tracking."""
        items = ["alpha", "beta", "gamma", "delta"]

        # Perform multiple mappings
        for i in range(5):
            engine.map(items)

        metrics = engine.get_adaptive_metrics()

        assert metrics['total_operations'] == 5
        assert 'total_processing_time' in metrics
        assert 'avg_processing_time' in metrics
        assert metrics['avg_processing_time'] > 0

    def test_cross_slot_coordination(self, engine):
        """Test cross-slot coordination via semantic mirror."""
        items = ["coordination test", "semantic mirror integration"]

        result = engine.map(items)

        # Should have attempted to publish constellation event
        engine.semantic_mirror.publish.assert_called()
        call_args = engine.semantic_mirror.publish.call_args

        # Verify event structure
        assert call_args[0][0] == 'slot05.constellation_mapped'  # key
        assert 'slot' in call_args[0][1]  # data
        assert call_args[0][1]['slot'] == 'slot05_constellation'


class TestEnhancedSlot5ConstellationAdapter:
    """Test suite for enhanced orchestrator adapter."""

    @pytest.fixture
    def adapter(self):
        """Create enhanced adapter for testing."""
        return EnhancedSlot5ConstellationAdapter()

    def test_adapter_initialization(self, adapter):
        """Test adapter initializes correctly."""
        assert adapter.available is not None
        assert adapter.engine_type in ['enhanced', 'base', 'none', 'error']

    def test_enhanced_mapping_interface(self, adapter):
        """Test enhanced mapping interface."""
        if not adapter.available:
            pytest.skip("Constellation engine not available")

        items = ["interface test", "adapter functionality", "orchestration layer"]
        context = {'stability_requirement': 'standard'}

        result = adapter.map(items, context)

        assert 'constellation' in result
        assert 'links' in result
        assert 'stability' in result

        # Enhanced adapter should include adaptive info
        if adapter.engine_type == 'enhanced':
            assert 'adaptive' in result

    def test_adaptive_metrics_retrieval(self, adapter):
        """Test adaptive metrics retrieval."""
        if not adapter.available:
            pytest.skip("Constellation engine not available")

        metrics = adapter.get_adaptive_metrics()
        assert 'engine_type' in metrics

        if adapter.engine_type == 'enhanced':
            assert 'total_operations' in metrics or 'adaptive_enabled' in metrics

    def test_configuration_management(self, adapter):
        """Test configuration retrieval and updates."""
        if not adapter.available:
            pytest.skip("Constellation engine not available")

        # Get current configuration
        config = adapter.get_configuration()
        assert 'engine_type' in config
        assert 'version' in config

        # Test configuration update
        if adapter.engine_type == 'enhanced':
            update_config = {
                'adaptive_config': {
                    'learning_rate': 0.05,
                    'adaptation_sensitivity': 0.03
                }
            }
            success = adapter.update_configuration(update_config)
            # Should succeed or gracefully handle if engine doesn't support updates
            assert isinstance(success, bool)

    def test_health_check_comprehensive(self, adapter):
        """Test comprehensive health check."""
        health = adapter.health_check()

        required_fields = ['available', 'engine_loaded', 'engine_type', 'status']
        for field in required_fields:
            assert field in health

        # Status should reflect capability level
        if health['available'] and health['engine_loaded']:
            assert health['status'] in ['structural', 'structural+', 'processual', 'degraded']
        else:
            assert health['status'] == 'unavailable'

    def test_processual_level_validation(self, adapter):
        """Test validation of Processual-level capabilities."""
        if not adapter.available or adapter.engine_type != 'enhanced':
            pytest.skip("Enhanced constellation engine not available")

        health = adapter.health_check()

        # Processual level requirements
        processual_requirements = [
            health.get('adaptive_enabled', False),
            health.get('cross_slot_coordination', False),
            'adaptive_metrics' in health or health.get('adaptive_enabled', False)
        ]

        # If all requirements met, should be Processual
        if all(processual_requirements):
            assert health['status'] == 'processual'

        # Test adaptive functionality
        if health.get('adaptive_enabled', False):
            metrics = adapter.get_adaptive_metrics()
            assert 'total_operations' in metrics or 'contexts_learned' in metrics


class TestProcessualCapabilityIntegration:
    """Integration tests for Processual-level capabilities."""

    def test_end_to_end_adaptive_processing(self):
        """Test complete adaptive processing workflow."""
        try:
            from orchestrator.semantic_mirror import get_semantic_mirror
            semantic_mirror = get_semantic_mirror()
        except Exception:
            semantic_mirror = MagicMock()
            semantic_mirror.publish = MagicMock(return_value=True)

        # Create full enhanced system
        engine = EnhancedConstellationEngine(semantic_mirror)
        adapter = EnhancedSlot5ConstellationAdapter()

        if not adapter.available or adapter.engine_type != 'enhanced':
            pytest.skip("Enhanced engine not available for integration test")

        # Simulate realistic workload with context variations
        test_scenarios = [
            {
                'items': ["sparse data", "limited connections"],
                'context': {'item_count': 2, 'stability_requirement': 'low'}
            },
            {
                'items': ["complex algorithm", "optimization technique", "performance metric",
                         "analysis method", "result interpretation"],
                'context': {'item_count': 5, 'stability_requirement': 'high'}
            },
            {
                'items': [f"item {i}" for i in range(20)],
                'context': {'item_count': 20, 'stability_requirement': 'standard'}
            }
        ]

        results = []
        for scenario in test_scenarios:
            result = adapter.map(scenario['items'], scenario['context'])
            results.append(result)

        # Verify adaptive behavior
        assert len(results) == 3

        # Should have different adaptive configurations for different contexts
        adaptive_configs = [r.get('adaptive', {}).get('thresholds_used', {}) for r in results]

        # At least some should be different (adaptive behavior)
        unique_configs = len(set(str(config) for config in adaptive_configs))
        assert unique_configs >= 2, "Adaptive system should produce different configurations for different contexts"

        # Verify learning occurred
        final_metrics = adapter.get_adaptive_metrics()
        if 'total_operations' in final_metrics:
            assert final_metrics['total_operations'] >= 3

        # Verify health reflects Processual capability
        health = adapter.health_check()
        if adapter.engine_type == 'enhanced':
            assert health['status'] in ['structural+', 'processual']


if __name__ == '__main__':
    pytest.main([__file__, '-v'])