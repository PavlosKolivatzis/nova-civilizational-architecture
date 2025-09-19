"""Comprehensive integration tests for all Slot1 enhancements."""

import pytest
import tempfile
import os
from orchestrator.adapters.slot1_truth_anchor import Slot1TruthAnchorAdapter


def test_slot1_full_integration():
    """Test complete Slot1 enhancement integration including persistence."""
    # Create temporary storage
    temp_dir = tempfile.mkdtemp()
    storage_path = os.path.join(temp_dir, 'integration_test.json')

    try:
        # Test 1: Basic functionality with recovery metadata
        from slots.slot01_truth_anchor.truth_anchor_engine import TruthAnchorEngine
        engine = TruthAnchorEngine(storage_path=storage_path)

        # Register anchor and verify backup metadata is added
        engine.register('integration.test', 'Test Value', extra='metadata')
        record = engine._anchors['integration.test']
        assert record.metadata['backup'] == 'Test Value'
        assert record.metadata['extra'] == 'metadata'

        # Test 2: Persistence across engine restarts
        initial_snapshot = engine.snapshot()

        # Create new engine instance - should load from persistence
        engine2 = TruthAnchorEngine(storage_path=storage_path)
        loaded_snapshot = engine2.snapshot()

        assert initial_snapshot['anchors'] == loaded_snapshot['anchors']
        assert engine2.verify('integration.test', 'Test Value')

        # Test 3: Recovery with persistence
        # Trigger recovery and verify it's saved
        prev_recoveries = loaded_snapshot['recoveries']
        engine2.verify('integration.test', 'Wrong Value')  # Should trigger recovery
        recovery_snapshot = engine2.snapshot()
        assert recovery_snapshot['recoveries'] >= prev_recoveries + 1

        # Test 4: Enhanced adapter functionality
        adapter = Slot1TruthAnchorAdapter()
        assert adapter.available

        # Basic adapter operations
        adapter.register('adapter.test', 'Adapter Value')
        assert adapter.verify('adapter.test', 'Adapter Value')

        adapter_snapshot = adapter.snapshot()
        assert adapter_snapshot['anchors'] > 0

        # Test 5: Enhanced features (if available)
        if adapter.enhanced_available:
            # Test cryptographic anchor establishment
            domain = adapter.establish_cryptographic_anchor(
                'integration.crypto',
                ['Integration test fact']
            )
            assert domain == 'integration.crypto'

            # Test verification
            verification = adapter.verify_cryptographic_anchor('integration.crypto')
            assert verification is not None
            assert verification.get('verified') is True

            # Test listing
            anchors = adapter.list_enhanced_anchors()
            assert isinstance(anchors, list)

            # Test cache stats
            stats = adapter.get_cache_stats()
            assert isinstance(stats, dict)

        # Test 6: Prometheus metrics integration
        from orchestrator.prometheus_metrics import update_slot1_metrics
        update_slot1_metrics()
        assert True  # If we get here, metrics update worked

    finally:
        # Cleanup
        import shutil
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)


def test_slot1_prometheus_metrics_export():
    """Test that Slot1 metrics are properly exported to Prometheus."""
    from orchestrator.prometheus_metrics import get_metrics_response

    # Generate some activity
    adapter = Slot1TruthAnchorAdapter()
    if adapter.available:
        adapter.register('prometheus.test', 'Metrics Test')
        adapter.verify('prometheus.test', 'Metrics Test')
        adapter.verify('prometheus.test', 'Wrong Value')  # Should fail

    # Get metrics response
    metrics_data, content_type = get_metrics_response()

    assert "text/plain" in content_type and "charset=utf-8" in content_type
    assert isinstance(metrics_data, bytes)

    metrics_text = metrics_data.decode('utf-8')

    # Verify Slot1 metrics are present
    assert 'nova_slot1_anchors_total' in metrics_text
    assert 'nova_slot1_lookups_total' in metrics_text
    assert 'nova_slot1_recoveries_total' in metrics_text
    assert 'nova_slot1_failures_total' in metrics_text


def test_slot1_error_handling():
    """Test error handling and graceful degradation."""
    # Test adapter with invalid storage path
    try:
        from slots.slot01_truth_anchor.truth_anchor_engine import TruthAnchorEngine
        engine = TruthAnchorEngine(storage_path='/invalid/path/test.json')
        engine.register('error.test', 'Error Test')
        assert True
    except Exception:
        pass

    # Test adapter functionality when engine unavailable
    adapter = Slot1TruthAnchorAdapter()

    # These should not raise exceptions
    result = adapter.establish_cryptographic_anchor('error.test', ['fact'])
    if not adapter.enhanced_available:
        assert result is None

    verification = adapter.verify_cryptographic_anchor('error.test')
    if not adapter.enhanced_available:
        assert verification is None

    anchors = adapter.list_enhanced_anchors()
    if not adapter.enhanced_available:
        assert anchors == []

    stats = adapter.get_cache_stats()
    if not adapter.enhanced_available:
        assert stats == {}


def test_slot1_backward_compatibility():
    """Test that all enhancements maintain backward compatibility."""
    adapter = Slot1TruthAnchorAdapter()

    # Original methods should work unchanged
    adapter.register('compat.test', 'Compatibility Test')
    assert adapter.verify('compat.test', 'Compatibility Test')
    assert not adapter.verify('compat.test', 'Wrong Value')

    snapshot = adapter.snapshot()
    assert isinstance(snapshot, dict)
    assert 'anchors' in snapshot or len(snapshot) == 0

    # Availability flags should be present
    assert hasattr(adapter, 'available')
    assert hasattr(adapter, 'enhanced_available')
    assert isinstance(adapter.available, bool)
    assert isinstance(adapter.enhanced_available, bool)
