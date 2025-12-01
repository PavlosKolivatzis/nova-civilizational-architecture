"""
Unit tests for Memory Resonance Window — Phase 7.0-RC

Tests 7-day rolling TRSI tracking, memory stability calculation,
and trend analysis.
"""
import pytest
import time
from nova.orchestrator.predictive.memory_resonance import (
    MemoryResonanceWindow,
    TRSISample,
    get_memory_window,
    reset_memory_window,
)


class TestTRSISample:
    """Test TRSI sample dataclass."""

    def test_sample_creation(self):
        """TRSI sample should store timestamp and value."""
        sample = TRSISample(timestamp=1.0, trsi_value=0.85, source="temporal_engine")

        assert sample.timestamp == 1.0
        assert sample.trsi_value == 0.85
        assert sample.source == "temporal_engine"

    def test_sample_default_source(self):
        """Default source should be temporal_engine."""
        sample = TRSISample(timestamp=1.0, trsi_value=0.85)
        assert sample.source == "temporal_engine"


class TestMemoryResonanceWindow:
    """Test memory resonance window with 7-day rolling buffer."""

    def test_initialization(self):
        """Window should initialize with correct capacity."""
        window = MemoryResonanceWindow(window_days=7)

        assert window.window_days == 7
        assert window.window_hours == 168
        assert len(window.trsi_history) == 0
        assert window.trsi_history.maxlen == 168

    def test_add_sample_basic(self):
        """Should add TRSI sample to history."""
        window = MemoryResonanceWindow()
        window.add_sample(trsi_value=0.85, timestamp=1.0)

        assert len(window.trsi_history) == 1
        assert window.trsi_history[0].trsi_value == 0.85
        assert window.trsi_history[0].timestamp == 1.0

    def test_add_sample_auto_timestamp(self):
        """Should auto-timestamp if not provided."""
        window = MemoryResonanceWindow()
        before = time.time()
        window.add_sample(trsi_value=0.85)
        after = time.time()

        assert len(window.trsi_history) == 1
        assert before <= window.trsi_history[0].timestamp <= after

    def test_add_sample_clamping(self):
        """Should clamp TRSI values to [0.0, 1.0]."""
        window = MemoryResonanceWindow()

        window.add_sample(trsi_value=1.5, timestamp=1.0)
        assert window.trsi_history[0].trsi_value == 1.0

        window.add_sample(trsi_value=-0.5, timestamp=2.0)
        assert window.trsi_history[1].trsi_value == 0.0

    def test_rolling_window_eviction(self):
        """Should evict oldest samples when exceeding capacity."""
        window = MemoryResonanceWindow(window_days=1)  # 24 hours
        assert window.trsi_history.maxlen == 24

        # Add 30 samples
        for i in range(30):
            window.add_sample(trsi_value=0.5 + (i * 0.01), timestamp=float(i))

        # Should keep only last 24
        assert len(window.trsi_history) == 24
        assert window.trsi_history[0].timestamp == 6.0  # First kept (30-24=6)
        assert window.trsi_history[-1].timestamp == 29.0  # Last added

    def test_compute_memory_stability_insufficient_data(self):
        """Should return 0.5 if <24 hours of data."""
        window = MemoryResonanceWindow()

        # Empty window
        assert window.compute_memory_stability() == 0.5

        # 10 samples (< 24)
        for i in range(10):
            window.add_sample(trsi_value=0.85, timestamp=float(i))
        assert window.compute_memory_stability() == 0.5

    def test_compute_memory_stability_stable_high(self):
        """Stable high TRSI should yield high stability."""
        window = MemoryResonanceWindow()

        # 100 samples, stable at 0.9
        for i in range(100):
            window.add_sample(trsi_value=0.9, timestamp=float(i))

        stability = window.compute_memory_stability()
        # mean=0.9, stdev=0.0 → stability=0.9
        assert stability == pytest.approx(0.9, abs=0.01)

    def test_compute_memory_stability_stable_low(self):
        """Stable low TRSI should yield low stability."""
        window = MemoryResonanceWindow()

        # 100 samples, stable at 0.4
        for i in range(100):
            window.add_sample(trsi_value=0.4, timestamp=float(i))

        stability = window.compute_memory_stability()
        # mean=0.4, stdev=0.0 → stability=0.4
        assert stability == pytest.approx(0.4, abs=0.01)

    def test_compute_memory_stability_volatile(self):
        """High volatility should reduce stability."""
        window = MemoryResonanceWindow()

        # 100 samples, alternating 0.3 and 0.9
        for i in range(100):
            trsi = 0.3 if i % 2 == 0 else 0.9
            window.add_sample(trsi_value=trsi, timestamp=float(i))

        stability = window.compute_memory_stability()
        # mean=0.6, stdev≈0.3 → stability≈0.3
        assert 0.2 <= stability <= 0.4

    def test_compute_memory_stability_clamping(self):
        """Stability should clamp to [0.0, 1.0]."""
        window = MemoryResonanceWindow()

        # Extreme volatility: stdev > mean
        for i in range(100):
            trsi = 0.0 if i % 2 == 0 else 1.0
            window.add_sample(trsi_value=trsi, timestamp=float(i))

        stability = window.compute_memory_stability()
        # mean=0.5, stdev=0.5 → stability=0.0 (clamped)
        assert stability == 0.0

    def test_get_trend_insufficient_data(self):
        """Should return 0.0 if <2 samples."""
        window = MemoryResonanceWindow()
        assert window.get_trend() == 0.0

        window.add_sample(trsi_value=0.85, timestamp=1.0)
        assert window.get_trend() == 0.0

    def test_get_trend_improving(self):
        """Should detect positive trend."""
        window = MemoryResonanceWindow()

        base_time = time.time()
        for i in range(30):
            window.add_sample(
                trsi_value=0.5 + (i * 0.01),  # Gradually increasing
                timestamp=base_time + (i * 3600)  # Hourly
            )

        trend = window.get_trend(hours=24)
        assert trend > 0.1  # Significant positive trend

    def test_get_trend_degrading(self):
        """Should detect negative trend."""
        window = MemoryResonanceWindow()

        base_time = time.time()
        for i in range(30):
            window.add_sample(
                trsi_value=0.9 - (i * 0.01),  # Gradually decreasing
                timestamp=base_time + (i * 3600)
            )

        trend = window.get_trend(hours=24)
        assert trend < -0.1  # Significant negative trend

    def test_get_window_stats_empty(self):
        """Should return neutral stats for empty window."""
        window = MemoryResonanceWindow()
        stats = window.get_window_stats()

        assert stats["count"] == 0
        assert stats["mean"] == 0.5
        assert stats["stdev"] == 0.0
        assert stats["stability"] == 0.5
        assert stats["window_start"] is None
        assert stats["window_end"] is None

    def test_get_window_stats_populated(self):
        """Should return comprehensive stats."""
        window = MemoryResonanceWindow()

        # Add 50 samples
        for i in range(50):
            window.add_sample(trsi_value=0.8 + (i * 0.001), timestamp=float(i))

        stats = window.get_window_stats()

        assert stats["count"] == 50
        assert stats["mean"] == pytest.approx(0.8245, abs=0.01)
        assert stats["stdev"] > 0.0
        assert 0.0 <= stats["stability"] <= 1.0
        assert stats["min"] >= 0.0
        assert stats["max"] <= 1.0
        assert stats["window_start"] == 0.0
        assert stats["window_end"] == 49.0

    def test_to_dict_serialization(self):
        """Should serialize window state to dict."""
        window = MemoryResonanceWindow(window_days=7)

        for i in range(30):
            window.add_sample(trsi_value=0.85, timestamp=float(i))

        data = window.to_dict()

        assert data["window_days"] == 7
        assert data["window_hours"] == 168
        assert data["samples"] == 30
        assert "memory_stability" in data
        assert "mean_trsi" in data
        assert "volatility" in data
        assert "trend_24h" in data
        assert "timestamp" in data


class TestMemoryWindowSingleton:
    """Test singleton memory window instance."""

    def test_get_memory_window_creates_instance(self):
        """Should create singleton instance."""
        reset_memory_window()  # Ensure clean state
        window = get_memory_window()

        assert isinstance(window, MemoryResonanceWindow)
        assert window.window_days == 7

    def test_get_memory_window_returns_same_instance(self):
        """Should return same instance across calls."""
        reset_memory_window()
        window1 = get_memory_window()
        window2 = get_memory_window()

        assert window1 is window2

    def test_reset_memory_window_clears_state(self):
        """Should reset singleton to fresh state."""
        window = get_memory_window()
        window.add_sample(trsi_value=0.85, timestamp=1.0)
        assert len(window.trsi_history) > 0

        reset_memory_window()
        window = get_memory_window()
        assert len(window.trsi_history) == 0


class TestMemoryResonanceIntegration:
    """Integration tests for memory resonance."""

    def test_full_7day_cycle(self):
        """Should handle full 7-day sampling cycle."""
        window = MemoryResonanceWindow(window_days=7)

        # Simulate hourly samples for 7 days
        base_time = time.time()
        for hour in range(168):  # 7 × 24
            trsi = 0.8 + (0.1 * (hour % 24) / 24)  # Daily cycle
            window.add_sample(trsi_value=trsi, timestamp=base_time + (hour * 3600))

        assert len(window.trsi_history) == 168
        stats = window.get_window_stats()
        assert stats["count"] == 168
        assert 0.7 <= stats["mean"] <= 0.9
        assert 0.0 <= stats["stability"] <= 1.0

    def test_continuous_sampling_with_eviction(self):
        """Should maintain 7-day window with continuous sampling."""
        window = MemoryResonanceWindow(window_days=7)

        # Sample for 10 days (should evict first 3 days)
        base_time = time.time()
        for hour in range(240):  # 10 days
            window.add_sample(trsi_value=0.85, timestamp=base_time + (hour * 3600))

        # Should keep only last 7 days (168 hours)
        assert len(window.trsi_history) == 168
        # First sample should be from day 4 (hour 72)
        assert window.trsi_history[0].timestamp >= base_time + (72 * 3600)
