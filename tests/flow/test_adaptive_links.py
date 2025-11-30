"""
Tests for Flow Fabric Adaptive Links

Validates AdaptiveLink wrapper behavior, weight/frequency adjustments, and metrics collection.
Ensures contract payload immutability and backward compatibility.
"""
import pytest
import time
from unittest.mock import Mock
from nova.orchestrator.adaptive_connections import AdaptiveLink, AdaptiveLinkConfig, adaptive_link_registry
from nova.orchestrator.flow_metrics import flow_metrics


class TestAdaptiveLink:
    """Test core AdaptiveLink functionality"""

    def setup_method(self):
        """Setup for each test"""
        self.contract_name = "EMOTION_REPORT@1"
        self.config = AdaptiveLinkConfig(adaptation_enabled=True)
        self.link = AdaptiveLink(self.contract_name, self.config)
        self.mock_send_func = Mock(return_value={"status": "success"})

    def test_adaptive_link_initialization(self):
        """Test adaptive link initializes with correct defaults"""
        assert self.link.contract_name == "EMOTION_REPORT@1"
        assert self.link.weight == 1.0
        assert self.link.frequency == 1.0
        assert self.link.config.adaptation_enabled
        assert self.link.metrics.sends_total == 0

    def test_basic_send_unchanged_behavior(self):
        """Test that AdaptiveLink doesn't modify basic send behavior when adaptation disabled"""
        # Disable adaptation
        self.link.config.adaptation_enabled = False

        payload = {"emotional_tone": "positive", "confidence": 0.85}
        original_payload = payload.copy()

        result = self.link.send(payload, self.mock_send_func)

        # Verify original send function called with unchanged payload
        self.mock_send_func.assert_called_once_with(payload)
        assert payload == original_payload  # Payload immutability
        assert result == {"status": "success"}

        # Verify metrics tracked even with adaptation disabled
        assert self.link.metrics.sends_total == 1
        assert self.link.metrics.sends_throttled == 0

    def test_send_with_adaptation_enabled(self):
        """Test AdaptiveLink behavior with adaptation enabled"""
        payload = {"emotional_tone": "negative", "confidence": 0.92}

        result = self.link.send(payload, self.mock_send_func)

        # Verify send completed successfully
        assert result == {"status": "success"}
        assert self.link.metrics.sends_total == 1
        assert len(self.link.send_history) == 1

        # Verify payload never modified
        self.mock_send_func.assert_called_once_with(payload)

        # Verify tracking recorded
        send_record = self.link.send_history[0]
        assert send_record["success"]
        assert send_record["weight"] == 1.0
        assert send_record["frequency"] == 1.0

    def test_weight_adjustment_within_bounds(self):
        """Test weight adjustment respects configured bounds"""
        # Test normal adjustment
        self.link.adjust_weight(1.5, "test increase")
        assert self.link.weight == 1.5
        assert self.link.metrics.weight_adjustments == 1

        # Test lower bound
        self.link.adjust_weight(0.05, "below minimum")  # Below min_weight (0.1)
        assert self.link.weight == 0.1  # Clamped to minimum

        # Test upper bound
        self.link.adjust_weight(5.0, "above maximum")   # Above max_weight (3.0)
        assert self.link.weight == 3.0  # Clamped to maximum

    def test_frequency_adjustment_within_bounds(self):
        """Test frequency adjustment respects configured bounds"""
        # Test normal adjustment
        self.link.adjust_frequency(0.8, "test decrease")
        assert self.link.frequency == 0.8
        assert self.link.metrics.frequency_adjustments == 1

        # Test bounds
        self.link.adjust_frequency(0.05, "below minimum")  # Below min_frequency (0.1)
        assert self.link.frequency == 0.1

        self.link.adjust_frequency(10.0, "above maximum")  # Above max_frequency (5.0)
        assert self.link.frequency == 5.0

    def test_frequency_throttling(self):
        """Test frequency-based throttling behavior"""
        # Set low frequency to trigger throttling
        self.link.adjust_frequency(0.5, "enable throttling")  # 0.5 = one send every 2 seconds

        payload = {"test": "data"}

        # First send should succeed
        result1 = self.link.send(payload, self.mock_send_func)
        assert result1 == {"status": "success"}
        assert self.link.metrics.sends_total == 1
        assert self.link.metrics.sends_throttled == 0

        # Immediate second send should be throttled
        result2 = self.link.send(payload, self.mock_send_func)
        assert result2 is None  # Throttled
        assert self.link.metrics.sends_total == 2
        assert self.link.metrics.sends_throttled == 1

        # Mock send function should only be called once (first send)
        assert self.mock_send_func.call_count == 1

    def test_adjustment_ignored_when_adaptation_disabled(self):
        """Test adjustments ignored when adaptation disabled"""
        self.link.config.adaptation_enabled = False

        original_weight = self.link.weight
        original_frequency = self.link.frequency

        self.link.adjust_weight(2.0, "should be ignored")
        self.link.adjust_frequency(2.0, "should be ignored")

        # Values should remain unchanged
        assert self.link.weight == original_weight
        assert self.link.frequency == original_frequency
        assert self.link.metrics.weight_adjustments == 0
        assert self.link.metrics.frequency_adjustments == 0

    def test_send_error_handling(self):
        """Test error handling and tracking in send operations"""
        # Mock send function that raises exception
        error_send_func = Mock(side_effect=ValueError("Test error"))
        payload = {"test": "data"}

        with pytest.raises(ValueError):
            self.link.send(payload, error_send_func)

        # Verify error tracked in history
        assert len(self.link.send_history) == 1
        error_record = self.link.send_history[0]
        assert not error_record["success"]
        assert error_record["error"] == "Test error"
        assert self.link.metrics.sends_total == 1

    def test_metrics_collection(self):
        """Test comprehensive metrics collection"""
        # Generate some activity
        payload = {"test": "data"}
        self.link.send(payload, self.mock_send_func)
        self.link.adjust_weight(1.2, "test")
        self.link.adjust_frequency(0.8, "test")

        metrics = self.link.get_metrics()

        # Verify all expected metrics present
        expected_keys = [
            "contract_name", "current_weight", "current_frequency",
            "sends_total", "sends_throttled", "weight_adjustments",
            "frequency_adjustments", "average_response_time",
            "last_adjustment_time", "adaptation_enabled", "history_size"
        ]

        for key in expected_keys:
            assert key in metrics

        assert metrics["contract_name"] == "EMOTION_REPORT@1"
        assert metrics["current_weight"] == 1.2
        assert metrics["current_frequency"] == 0.8
        assert metrics["sends_total"] == 1
        assert metrics["weight_adjustments"] == 1
        assert metrics["frequency_adjustments"] == 1


class TestAdaptiveLinkRegistry:
    """Test adaptive link registry functionality"""

    def setup_method(self):
        """Setup for each test"""
        # Clear registry for clean tests
        adaptive_link_registry.links.clear()

    def test_registry_get_or_create_link(self):
        """Test registry creates and reuses links correctly"""
        contract_name = "TEST_REPORT@1"

        # First call should create new link
        link1 = adaptive_link_registry.get_link(contract_name)
        assert link1.contract_name == contract_name
        assert len(adaptive_link_registry.links) == 1

        # Second call should return same link
        link2 = adaptive_link_registry.get_link(contract_name)
        assert link1 is link2  # Same object reference
        assert len(adaptive_link_registry.links) == 1

    def test_registry_global_adaptation_control(self):
        """Test global adaptation enable/disable"""
        # Create a few links
        link1 = adaptive_link_registry.get_link("CONTRACT_A@1")
        link2 = adaptive_link_registry.get_link("CONTRACT_B@1")

        # Enable adaptation globally
        adaptive_link_registry.set_global_adaptation_enabled(True)
        assert link1.config.adaptation_enabled
        assert link2.config.adaptation_enabled

        # Disable adaptation globally
        adaptive_link_registry.set_global_adaptation_enabled(False)
        assert not link1.config.adaptation_enabled
        assert not link2.config.adaptation_enabled

    def test_registry_metrics_collection(self):
        """Test registry aggregates metrics from all links"""
        # Create and use multiple links with adaptation enabled
        link1 = adaptive_link_registry.get_link("CONTRACT_A@1")
        link1.config.adaptation_enabled = True  # Enable adaptation for adjustments
        link2 = adaptive_link_registry.get_link("CONTRACT_B@1")

        # Generate some activity
        mock_send = Mock(return_value={"status": "ok"})
        link1.send({"data": "test1"}, mock_send)
        link2.send({"data": "test2"}, mock_send)
        link1.adjust_weight(1.5, "test")

        all_metrics = adaptive_link_registry.get_all_metrics()

        assert len(all_metrics) == 2
        contract_names = {m["contract_name"] for m in all_metrics}
        assert contract_names == {"CONTRACT_A@1", "CONTRACT_B@1"}

        # Find metrics for CONTRACT_A@1
        a_metrics = next(m for m in all_metrics if m["contract_name"] == "CONTRACT_A@1")
        assert a_metrics["sends_total"] == 1
        assert a_metrics["weight_adjustments"] == 1


class TestFlowMetrics:
    """Test flow metrics collection and formatting"""

    def setup_method(self):
        """Setup for each test"""
        adaptive_link_registry.links.clear()

    def test_prometheus_metrics_format(self):
        """Test Prometheus metrics format generation"""
        # Create link with some activity and adaptation enabled
        link = adaptive_link_registry.get_link("EMOTION_REPORT@1")
        link.config.adaptation_enabled = True  # Enable for weight adjustments
        mock_send = Mock(return_value={"status": "ok"})
        link.send({"test": "data"}, mock_send)
        link.adjust_weight(1.3, "test")

        prometheus_output = flow_metrics.get_metrics_for_prometheus()

        # Verify Prometheus format (use current weight after adjustment)
        assert 'adaptive_link_weight{contract="EMOTION_REPORT@1"} 1.3' in prometheus_output
        assert 'adaptive_link_frequency{contract="EMOTION_REPORT@1"} 1.0' in prometheus_output
        assert 'adaptive_link_sends_total{contract="EMOTION_REPORT@1"} 1' in prometheus_output
        assert "# HELP adaptive_link_weight" in prometheus_output
        assert "# TYPE adaptive_link_weight gauge" in prometheus_output

    def test_flow_health_summary(self):
        """Test flow health summary for /health endpoint"""
        # Test with no links
        health = flow_metrics.get_flow_health_summary()
        assert not health["adaptive_connections_active"]
        assert health["links_count"] == 0
        assert health["status"] == "no_links"

        # Test with active links
        link = adaptive_link_registry.get_link("EMOTION_REPORT@1")
        link.config.adaptation_enabled = True
        mock_send = Mock(return_value={"status": "ok"})
        link.send({"test": "data"}, mock_send)

        health = flow_metrics.get_flow_health_summary()
        assert health["adaptive_connections_active"]
        assert health["links_count"] == 1
        assert health["adaptation_enabled_links"] == 1
        assert health["total_sends"] == 1
        assert health["contracts_tracked"] == ["EMOTION_REPORT@1"]
        assert health["status"] in ["healthy", "adaptation_disabled"]


@pytest.mark.integration
class TestS3ToS6Integration:
    """Integration tests for S3→S6 EMOTION_REPORT@1 adaptive link"""

    def test_emotion_report_adaptive_wrapper(self):
        """Test AdaptiveLink wrapper around S3→S6 emotion report flow"""
        # This would be expanded with actual S3/S6 adapter integration
        # For now, test the wrapper pattern

        def mock_s3_to_s6_send(payload):
            # Simulate S3→S6 emotion report send
            assert "emotional_tone" in payload
            assert "confidence" in payload
            return {"synthesis_result": "processed", "status": "success"}

        # Clear registry to ensure clean state
        adaptive_link_registry.links.clear()

        # Create adaptive link for emotion reports
        emotion_link = adaptive_link_registry.get_link("EMOTION_REPORT@1")
        emotion_link.config.adaptation_enabled = True

        # Test wrapped send
        emotion_payload = {
            "emotional_tone": "concern",
            "confidence": 0.88,
            "timestamp": time.time()
        }

        result = emotion_link.send(emotion_payload, mock_s3_to_s6_send)

        assert result["status"] == "success"
        assert emotion_link.metrics.sends_total == 1

        # Test adaptation behavior
        emotion_link.adjust_weight(1.4, "elevated concern level")
        assert emotion_link.weight == 1.4

        # Verify metrics available for monitoring
        metrics = emotion_link.get_metrics()
        assert metrics["contract_name"] == "EMOTION_REPORT@1"
        assert metrics["current_weight"] == 1.4
