"""Test entropy monitor robustness with small samples and edge cases."""

import time
import pytest

# Handle imports for both pytest and direct execution
try:
    from ..core.entropy_monitor import EntropyMonitor
except ImportError:
    import sys
    from pathlib import Path
    sys.path.append(str(Path(__file__).parent.parent))
    from core.entropy_monitor import EntropyMonitor


class TestEntropyMonitorSmallSamples:
    """Test entropy monitor handles small samples gracefully."""

    def test_temporal_entropy_handles_small_samples(self):
        """Test temporal entropy calculation with insufficient data points."""
        monitor = EntropyMonitor(window_size=5)

        # Test with 1 timestamp -> should return 0 entropy without crashing
        monitor.timestamps.append(time.time())
        monitor.operation_types.append("write")
        monitor.schema_hashes.append("hash1")
        monitor.content_sizes.append(100)

        score = monitor._calculate_entropy_score()
        assert 0.0 <= score <= 1.0, "Score should be in valid range"
        assert isinstance(score, float), "Score should be a float"

    def test_temporal_entropy_with_two_timestamps(self):
        """Test temporal entropy with exactly 2 timestamps (insufficient for stdev)."""
        monitor = EntropyMonitor(window_size=5)

        base_time = time.time()
        monitor.timestamps.extend([base_time, base_time + 1.0])
        monitor.operation_types.extend(["write", "read"])
        monitor.schema_hashes.extend(["hash1", "hash2"])
        monitor.content_sizes.extend([100, 200])

        score = monitor._calculate_entropy_score()
        assert 0.0 <= score <= 1.0, "Score should be in valid range"
        assert isinstance(score, float), "Score should be a float"

    def test_temporal_entropy_with_enough_samples(self):
        """Test temporal entropy with sufficient data points."""
        monitor = EntropyMonitor(window_size=10)

        base_time = time.time()
        timestamps = [base_time + i * 1.5 for i in range(5)]  # 5 timestamps = 4 deltas

        monitor.timestamps.extend(timestamps)
        monitor.operation_types.extend(["write"] * 5)
        monitor.schema_hashes.extend([f"hash{i}" for i in range(5)])
        monitor.content_sizes.extend([100 + i * 10 for i in range(5)])

        score = monitor._calculate_entropy_score()
        assert 0.0 <= score <= 1.0, "Score should be in valid range"
        assert isinstance(score, float), "Score should be a float"

    def test_temporal_entropy_with_duplicate_timestamps(self):
        """Test temporal entropy handles duplicate/zero deltas."""
        monitor = EntropyMonitor(window_size=10)

        base_time = time.time()
        # Include duplicate timestamps (zero deltas)
        timestamps = [base_time, base_time, base_time + 1.0, base_time + 2.0]

        monitor.timestamps.extend(timestamps)
        monitor.operation_types.extend(["write"] * 4)
        monitor.schema_hashes.extend([f"hash{i}" for i in range(4)])
        monitor.content_sizes.extend([100] * 4)

        score = monitor._calculate_entropy_score()
        assert 0.0 <= score <= 1.0, "Score should be in valid range"
        assert isinstance(score, float), "Score should be a float"

    def test_temporal_entropy_with_negative_deltas(self):
        """Test temporal entropy handles clock jumps (negative deltas)."""
        monitor = EntropyMonitor(window_size=10)

        base_time = time.time()
        # Simulate clock jump backwards
        timestamps = [base_time, base_time + 1.0, base_time - 1.0, base_time + 2.0]

        monitor.timestamps.extend(timestamps)
        monitor.operation_types.extend(["write"] * 4)
        monitor.schema_hashes.extend([f"hash{i}" for i in range(4)])
        monitor.content_sizes.extend([100] * 4)

        score = monitor._calculate_entropy_score()
        assert 0.0 <= score <= 1.0, "Score should be in valid range"
        assert isinstance(score, float), "Score should be a float"

    def test_empty_monitor_state(self):
        """Test entropy calculation with completely empty state."""
        monitor = EntropyMonitor(window_size=5)

        score = monitor._calculate_entropy_score()
        assert score == 0.0, "Empty monitor should return 0 entropy"
        assert isinstance(score, float), "Score should be a float"

    def test_update_method_with_small_samples(self):
        """Test the public update method handles small samples."""
        monitor = EntropyMonitor(window_size=5)

        # Single update
        score1 = monitor.update({"test": 1}, "operation1")
        assert 0.0 <= score1 <= 1.0, "First update should be valid"

        # Second update
        score2 = monitor.update({"test": 2}, "operation2")
        assert 0.0 <= score2 <= 1.0, "Second update should be valid"

        # Third update (now we have 3 points, could calculate temporal variance)
        score3 = monitor.update({"test": 3}, "operation3")
        assert 0.0 <= score3 <= 1.0, "Third update should be valid"

    def test_is_anomalous_with_small_samples(self):
        """Test anomaly detection works with small samples."""
        monitor = EntropyMonitor(window_size=5, entropy_threshold=0.5)

        # Test with no data
        assert not monitor.is_anomalous(), "Empty monitor should not be anomalous"

        # Test with minimal data
        monitor.update({"simple": "data"}, "test")
        result = monitor.is_anomalous()
        assert isinstance(result, bool), "Should return boolean"

    def test_get_metrics_with_small_samples(self):
        """Test metrics gathering with small samples."""
        monitor = EntropyMonitor(window_size=5)

        # Empty state
        metrics = monitor.get_metrics()
        assert isinstance(metrics, dict), "Should return dict"
        assert "current_entropy" in metrics, "Should include entropy"
        assert 0.0 <= metrics["current_entropy"] <= 1.0, "Entropy should be valid"

        # Single update
        monitor.update({"test": 1}, "op1")
        metrics = monitor.get_metrics()
        assert isinstance(metrics, dict), "Should return dict after update"

    def test_reset_functionality(self):
        """Test reset clears state properly."""
        monitor = EntropyMonitor(window_size=5)

        # Add some data
        for i in range(3):
            monitor.update({"data": i}, f"op{i}")

        # Verify data exists
        assert len(monitor.schema_hashes) > 0, "Should have data before reset"

        # Reset
        monitor.reset()

        # Verify state is clean
        assert len(monitor.schema_hashes) == 0, "Should be empty after reset"
        assert len(monitor.timestamps) == 0, "Should be empty after reset"

        # Verify it still works
        score = monitor._calculate_entropy_score()
        assert score == 0.0, "Should return 0 after reset"

    def test_adaptive_threshold_with_small_samples(self):
        """Test adaptive threshold updates don't crash with small samples."""
        monitor = EntropyMonitor(window_size=5)

        # Test threshold adaptation with minimal data
        initial_threshold = monitor.adaptive_entropy_threshold

        # Single update
        monitor.update({"test": 1}, "op1")

        # Should not crash and threshold should be reasonable
        assert isinstance(monitor.adaptive_entropy_threshold, float)
        assert 0.0 <= monitor.adaptive_entropy_threshold <= 1.0

    def test_pattern_analysis_with_small_samples(self):
        """Test pattern analysis handles small samples."""
        monitor = EntropyMonitor(window_size=5)

        # Empty analysis
        analysis = monitor.get_pattern_analysis()
        assert isinstance(analysis, dict), "Should return dict"

        # Single sample analysis
        monitor.update({"test": 1}, "op1")
        analysis = monitor.get_pattern_analysis()
        assert isinstance(analysis, dict), "Should handle single sample"

        # Multiple samples
        for i in range(3):
            monitor.update({"data": i}, f"op{i}")

        analysis = monitor.get_pattern_analysis()
        assert isinstance(analysis, dict), "Should handle multiple samples"
        assert "pattern_stability" in analysis, "Should include stability metric"


def test_comprehensive_edge_cases():
    """Comprehensive test of edge cases."""
    monitor = EntropyMonitor(window_size=3)  # Small window for faster testing

    edge_cases = [
        # Empty object
        {},
        # None values
        {"key": None},
        # Large nested structure
        {"nested": {"deep": {"structure": list(range(100))}}},
        # Very long string
        {"long_string": "x" * 10000},
        # Mixed types
        {"string": "test", "number": 42, "list": [1, 2, 3], "bool": True},
    ]

    for i, obj in enumerate(edge_cases):
        try:
            score = monitor.update(obj, f"edge_case_{i}")
            assert 0.0 <= score <= 1.0, f"Edge case {i} produced invalid score: {score}"
        except Exception as e:
            pytest.fail(f"Edge case {i} raised exception: {e}")


if __name__ == "__main__":
    # Run basic tests
    print("Running entropy monitor small sample tests...")

    test = TestEntropyMonitorSmallSamples()

    test.test_temporal_entropy_handles_small_samples()
    print("✓ Small samples test passed")

    test.test_temporal_entropy_with_two_timestamps()
    print("✓ Two timestamps test passed")

    test.test_temporal_entropy_with_enough_samples()
    print("✓ Sufficient samples test passed")

    test.test_update_method_with_small_samples()
    print("✓ Update method test passed")

    test_comprehensive_edge_cases()
    print("✓ Edge cases test passed")

    print("All entropy monitor robustness tests passed!")