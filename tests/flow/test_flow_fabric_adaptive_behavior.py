"""Flow fabric adaptive behavior tests with health-influenced routing.

Tests adaptive connections behavior under different health conditions,
validating that flow fabric responds appropriately to health changes
from the polish sprint health modules.
"""

import pytest
import time
import os
from unittest.mock import patch, MagicMock


class TestFlowFabricHealthResponsiveness:
    """Test flow fabric adaptive behavior based on health signals."""

    def test_adaptive_connections_respond_to_health_degradation(self):
        """Test that adaptive connections throttle when health degrades."""
        from orchestrator.adaptive_connections import adaptive_link_registry, AdaptiveLinkConfig

        # Enable adaptive connections
        config = AdaptiveLinkConfig(adaptation_enabled=True, base_frequency=1.0)
        link = adaptive_link_registry.get_link("EMOTION_REPORT@1", config)

        # Mock original send function
        mock_send = MagicMock(return_value={"status": "success"})

        # Simulate healthy state - should send normally
        healthy_payload = {"emotional_state": "positive", "confidence": 0.95}
        result = link.send(healthy_payload, mock_send)

        assert result == {"status": "success"}
        assert mock_send.called
        mock_send.reset_mock()

        # Simulate degraded health - adjust frequency downward
        link.adjust_frequency(0.3, "health_degradation")

        # Fast subsequent sends should be throttled
        start_time = time.time()
        for _ in range(3):
            result = link.send(healthy_payload, mock_send)
            time.sleep(0.1)  # Brief pause

        # Some sends should be throttled (returning None)
        assert link.metrics.sends_throttled > 0

    def test_adaptive_links_weight_adjustment_with_health(self):
        """Test weight adjustment based on slot health status."""
        from orchestrator.adaptive_connections import adaptive_link_registry, AdaptiveLinkConfig

        # Enable adaptive connections
        config = AdaptiveLinkConfig(adaptation_enabled=True, base_weight=1.0)
        link = adaptive_link_registry.get_link("TRI_REPORT@1", config)

        initial_weight = link.weight

        # Simulate healthy slot - increase weight
        link.adjust_weight(2.0, "slot_healthy")
        assert link.weight > initial_weight

        # Simulate degraded slot - decrease weight
        link.adjust_weight(0.5, "slot_degraded")
        assert link.weight < initial_weight

        # Check metrics tracking
        assert link.metrics.weight_adjustments >= 2

    def test_flow_fabric_health_integration_end_to_end(self):
        """Test end-to-end flow fabric behavior with health integration."""
        from orchestrator.health import health_payload
        from orchestrator.core.performance_monitor import PerformanceMonitor
        from orchestrator.core import create_router
        from orchestrator.flow_fabric_init import initialize_flow_fabric
        import pkgutil
        import slots

        # Initialize flow fabric
        initialize_flow_fabric()

        # Get current health status
        slot_registry = {
            name: None
            for _, name, _ in pkgutil.iter_modules(slots.__path__)
            if name.startswith("slot")
        }

        monitor = PerformanceMonitor()
        router = create_router(monitor)
        payload = health_payload(slot_registry, monitor, router, None)

        # Verify flow fabric is reporting with health context
        assert "flow_fabric" in payload
        flow_fabric = payload["flow_fabric"]

        # Should have adaptive connections active
        assert "adaptive_connections_active" in flow_fabric
        assert "links_count" in flow_fabric
        assert flow_fabric["links_count"] > 0

        # Status should reflect health state
        assert flow_fabric["status"] in ["healthy", "degraded", "adaptation_disabled", "high_throttling"]

    def test_contract_prioritization_based_on_health(self):
        """Test that contracts are prioritized based on slot health."""
        from orchestrator.adaptive_connections import adaptive_link_registry, AdaptiveLinkConfig

        # Create links for different contracts
        contracts = ["EMOTION_REPORT@1", "TRI_REPORT@1", "CULTURAL_PROFILE@1"]
        links = {}

        for contract in contracts:
            config = AdaptiveLinkConfig(adaptation_enabled=True, base_weight=1.0)
            links[contract] = adaptive_link_registry.get_link(contract, config)

        # Simulate health-based prioritization
        # Healthy emotional analysis - high priority
        links["EMOTION_REPORT@1"].adjust_weight(2.5, "slot03_healthy")

        # Degraded TRI analysis - low priority
        links["TRI_REPORT@1"].adjust_weight(0.3, "slot04_degraded")

        # Normal cultural synthesis
        links["CULTURAL_PROFILE@1"].adjust_weight(1.0, "slot06_normal")

        # Verify prioritization
        assert links["EMOTION_REPORT@1"].weight > links["CULTURAL_PROFILE@1"].weight
        assert links["CULTURAL_PROFILE@1"].weight > links["TRI_REPORT@1"].weight


class TestFlowFabricPolishSprintIntegration:
    """Test flow fabric integration with polish sprint improvements."""

    def test_flow_fabric_recognizes_new_slot_capabilities(self):
        """Test that flow fabric adapts to new slot capabilities from polish sprint."""
        from orchestrator.flow_fabric_init import KNOWN_CONTRACTS

        # Verify all expected contracts are known
        expected_contracts = [
            "TRI_REPORT@1",           # slot04 → slot02, slot05
            "EMOTION_REPORT@1",       # slot03 → slot06
            "CULTURAL_PROFILE@1",     # slot06 → slot02, slot10
            "DETECTION_REPORT@1",     # slot09 → slot02
            "CONSTELLATION_REPORT@1", # slot05 → slot06
            "DELTA_THREAT@1",         # slot02 → slot04
            "PRODUCTION_CONTROL@1",   # slot07 → All slots
            "META_LENS_REPORT@1",     # slot08 → slot06
            "CONSTELLATION_STATE@1",  # slot05 → slot04
            # SIGNALS@1 removed - legacy contract with no producer/consumer (DEF-028)
        ]

        for contract in expected_contracts:
            assert contract in KNOWN_CONTRACTS

        # Should have 9 known contracts (SIGNALS@1 removed in DEF-028)
        assert len(KNOWN_CONTRACTS) == 9

    def test_flow_fabric_handles_polish_sprint_health_states(self):
        """Test flow fabric adaptation to polish sprint health states."""
        from orchestrator.adaptive_connections import adaptive_link_registry, AdaptiveLinkConfig

        # Test with realistic polish sprint health scenarios
        health_scenarios = [
            {
                "slot02_deltathresh": {"self_check": "ok", "engine_status": "normal"},
                "slot04_tri": {"self_check": "error", "engine_status": "degraded"},
                "slot08_memory_lock": {"self_check": "ok", "engine_status": "normal"},
                "expected_behavior": "reduce_tri_weight"
            },
            {
                "slot09_distortion_protection": {"self_check": "ok", "engine_status": "normal"},
                "slot10_civilizational_deployment": {"self_check": "ok", "engine_status": "normal"},
                "expected_behavior": "maintain_normal_weights"
            }
        ]

        for scenario in health_scenarios:
            # Get links for testing
            config = AdaptiveLinkConfig(adaptation_enabled=True)
            tri_link = adaptive_link_registry.get_link("TRI_REPORT@1", config)
            detection_link = adaptive_link_registry.get_link("DETECTION_REPORT@1", config)

            initial_tri_weight = tri_link.weight
            initial_detection_weight = detection_link.weight

            # Simulate health-based adjustments
            if scenario["expected_behavior"] == "reduce_tri_weight":
                # Ensure we start from a higher weight
                tri_link.adjust_weight(1.5, "reset_weight")
                initial_tri_weight = tri_link.weight
                tri_link.adjust_weight(0.5, "slot04_degraded")
                assert tri_link.weight < initial_tri_weight

            elif scenario["expected_behavior"] == "maintain_normal_weights":
                # No adjustment needed for healthy state
                assert tri_link.weight == initial_tri_weight
                assert detection_link.weight == initial_detection_weight

    def test_flow_fabric_metrics_during_health_transitions(self):
        """Test flow fabric metrics during health state transitions."""
        from orchestrator.adaptive_connections import get_flow_health_summary

        # Get initial metrics
        initial_summary = get_flow_health_summary()

        assert "adaptive_connections_active" in initial_summary
        assert "links_count" in initial_summary
        assert "status" in initial_summary

        # Should handle metrics collection gracefully
        assert isinstance(initial_summary["links_count"], int)
        assert initial_summary["status"] in ["healthy", "degraded", "no_links"]


class TestFlowFabricConfigurationValidation:
    """Test flow fabric configuration with polish sprint settings."""

    def test_adaptive_links_config_loading(self):
        """Test loading of adaptive links configuration."""
        from orchestrator.flow_fabric_init import load_adaptive_links_config

        config = load_adaptive_links_config()
        assert isinstance(config, dict)

        # Should handle missing config gracefully
        assert config is not None

    def test_environment_flag_behavior(self):
        """Test flow fabric behavior under different environment flags."""
        with patch.dict(os.environ, {"NOVA_ADAPTIVE_CONNECTIONS_ENABLED": "true"}):
            from orchestrator.adaptive_connections import get_flow_health_summary

            summary = get_flow_health_summary()
            assert summary["adaptive_connections_active"] is True

        with patch.dict(os.environ, {"NOVA_ADAPTIVE_CONNECTIONS_ENABLED": "false"}):
            from orchestrator.adaptive_connections import get_flow_health_summary

            summary = get_flow_health_summary()
            assert summary["adaptive_connections_active"] is False

    def test_flow_fabric_contract_registration(self):
        """Test that all contracts get registered properly."""
        from orchestrator.flow_fabric_init import initialize_flow_fabric, get_flow_fabric_status

        # Initialize flow fabric
        initialize_flow_fabric()

        # Check registration status
        status = get_flow_fabric_status()

        assert status["initialized"] is True
        assert status["total_links"] >= 9  # Should have all known contracts (9 after SIGNALS@1 removal)
        assert len(status["contracts_registered"]) >= 9  # 9 contracts after SIGNALS@1 removal


class TestFlowFabricErrorHandling:
    """Test flow fabric error handling and resilience."""

    def test_flow_fabric_handles_missing_health_data(self):
        """Test flow fabric graceful handling when health data is missing."""
        from orchestrator.adaptive_connections import adaptive_link_registry, AdaptiveLinkConfig

        # Create link without health context
        config = AdaptiveLinkConfig(adaptation_enabled=True)
        link = adaptive_link_registry.get_link("TEST_CONTRACT@1", config)

        # Should initialize with default values
        assert link.weight == config.base_weight
        assert link.frequency == config.base_frequency

        # Should handle adjustments gracefully
        link.adjust_weight(1.5, "test_adjustment")
        assert link.weight == 1.5

    def test_flow_fabric_disabled_adaptation_fallback(self):
        """Test flow fabric behavior when adaptation is disabled."""
        from orchestrator.adaptive_connections import adaptive_link_registry, AdaptiveLinkConfig

        # Create link with adaptation disabled
        config = AdaptiveLinkConfig(adaptation_enabled=False)
        link = adaptive_link_registry.get_link("DISABLED_TEST@1", config)

        initial_weight = link.weight
        initial_frequency = link.frequency

        # Adjustments should be ignored
        link.adjust_weight(2.0, "should_be_ignored")
        link.adjust_frequency(0.5, "should_be_ignored")

        assert link.weight == initial_weight
        assert link.frequency == initial_frequency

    def test_flow_fabric_performance_under_load(self):
        """Test flow fabric performance under simulated load."""
        from orchestrator.adaptive_connections import adaptive_link_registry, AdaptiveLinkConfig

        config = AdaptiveLinkConfig(adaptation_enabled=True)
        link = adaptive_link_registry.get_link("LOAD_TEST@1", config)

        mock_send = MagicMock(return_value={"status": "success"})
        payload = {"test": "data"}

        # Measure performance over multiple sends
        start_time = time.perf_counter()

        for i in range(100):
            result = link.send(payload, mock_send)

        end_time = time.perf_counter()
        total_time = end_time - start_time

        # Should handle 100 sends efficiently (< 1 second)
        assert total_time < 1.0

        # Should have metrics for all sends
        assert link.metrics.sends_total >= 100


class TestFlowFabricHealthAwareness:
    """Test flow fabric awareness of health signals from polish sprint slots."""

    def test_flow_fabric_responds_to_slot_health_changes(self):
        """Test that flow fabric adapts behavior based on slot health changes."""
        from orchestrator.adaptive_connections import adaptive_link_registry, AdaptiveLinkConfig

        # Create links for polish sprint slots
        slot_links = {
            "slot02": adaptive_link_registry.get_link("DELTA_THREAT@1", AdaptiveLinkConfig(adaptation_enabled=True)),
            "slot04": adaptive_link_registry.get_link("TRI_REPORT@1", AdaptiveLinkConfig(adaptation_enabled=True)),
            "slot08": adaptive_link_registry.get_link("META_LENS_REPORT@1", AdaptiveLinkConfig(adaptation_enabled=True)),
            "slot09": adaptive_link_registry.get_link("DETECTION_REPORT@1", AdaptiveLinkConfig(adaptation_enabled=True)),
            "slot10": adaptive_link_registry.get_link("CULTURAL_PROFILE@1", AdaptiveLinkConfig(adaptation_enabled=True))
        }

        # Simulate health degradation in slot04 (TRI)
        slot_links["slot04"].adjust_weight(0.2, "tri_engine_degraded")
        slot_links["slot04"].adjust_frequency(0.3, "tri_processing_slow")

        # Simulate healthy operation in slot02 (ΔTHRESH)
        slot_links["slot02"].adjust_weight(1.8, "deltathresh_optimal")

        # Verify adaptive responses
        assert slot_links["slot04"].weight < 0.5  # Reduced priority for degraded TRI
        assert slot_links["slot02"].weight > 1.5  # Increased priority for healthy ΔTHRESH

        # All links should track their adjustments
        for link in slot_links.values():
            assert hasattr(link.metrics, 'weight_adjustments')
            assert hasattr(link.metrics, 'frequency_adjustments')