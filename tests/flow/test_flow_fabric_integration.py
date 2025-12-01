# tests/flow/test_flow_fabric_integration.py
"""
Integration tests for the Flow Fabric.

Covers:
- init + contract registration
- config loading/merging
- health payload integration
- adaptive link registry + metrics
- env-flag behavior
- graceful failure paths
"""

import os
from unittest.mock import patch

import pytest


class TestFlowFabricInitialization:
    """Flow fabric initialization and contract registration."""

    def test_flow_fabric_init_imports(self):
        from nova.orchestrator.flow_fabric_init import initialize_flow_fabric, KNOWN_CONTRACTS

        assert callable(initialize_flow_fabric)
        assert isinstance(KNOWN_CONTRACTS, list)
        assert len(KNOWN_CONTRACTS) == 9  # SIGNALS@1 removed (DEF-028)

    def test_known_contracts_format(self):
        from nova.orchestrator.flow_fabric_init import KNOWN_CONTRACTS

        expected_contracts = [
            "TRI_REPORT@1",
            "EMOTION_REPORT@1",
            "CULTURAL_PROFILE@1",
            "DETECTION_REPORT@1",
            "CONSTELLATION_REPORT@1",
            "DELTA_THREAT@1",
            "PRODUCTION_CONTROL@1",
            "META_LENS_REPORT@1",
            "CONSTELLATION_STATE@1",
            # SIGNALS@1 removed - legacy contract with no producer/consumer (DEF-028)
        ]
        assert KNOWN_CONTRACTS == expected_contracts

    def test_config_loading(self):
        from nova.orchestrator.flow_fabric_init import load_adaptive_links_config

        config = load_adaptive_links_config()
        assert isinstance(config, dict)

    def test_adaptive_link_config_creation(self):
        from nova.orchestrator.flow_fabric_init import create_adaptive_link_config

        config_data = {
            "adaptive_connections_enabled": True,
            "default_config": {
                "base_weight": 1.0,
                "base_frequency": 1.0,
                "min_weight": 0.1,
                "max_weight": 3.0,
            },
            "contracts": {
                "TRI_REPORT@1": {
                    "base_weight": 1.5,
                    "priority": "high",
                }
            },
        }

        link_config = create_adaptive_link_config("TRI_REPORT@1", config_data)
        assert link_config.base_weight == 1.5  # contract override
        assert link_config.adaptation_enabled is True

    def test_initialize_flow_fabric_execution(self):
        # Should run without exceptions even if no external config is present.
        from nova.orchestrator.flow_fabric_init import initialize_flow_fabric

        try:
            initialize_flow_fabric()
        except Exception as e:  # pragma: no cover - defensive
            pytest.fail(f"Flow fabric initialization failed: {e}")

    def test_flow_fabric_status_function(self):
        from nova.orchestrator.flow_fabric_init import get_flow_fabric_status

        status = get_flow_fabric_status()
        assert isinstance(status, dict)
        for key in ("initialized", "total_links", "contracts_registered", "known_contracts", "registration_coverage"):
            assert key in status

        assert status["known_contracts"] == [
            "TRI_REPORT@1",
            "EMOTION_REPORT@1",
            "CULTURAL_PROFILE@1",
            "DETECTION_REPORT@1",
            "CONSTELLATION_REPORT@1",
            "DELTA_THREAT@1",
            "PRODUCTION_CONTROL@1",
            "META_LENS_REPORT@1",
            "CONSTELLATION_STATE@1",
            # SIGNALS@1 removed - legacy contract with no producer/consumer (DEF-028)
        ]


class TestFlowFabricHealthIntegration:
    """Flow fabric integration with the health system."""

    def test_flow_fabric_health_reporting(self):
        from nova.orchestrator.health import health_payload
        from nova.orchestrator.core.performance_monitor import PerformanceMonitor
        from nova.orchestrator.core import create_router

        monitor = PerformanceMonitor()
        router = create_router(monitor)
        slot_registry = {}

        payload = health_payload(slot_registry, monitor, router, None)
        assert "flow_fabric" in payload

        flow_fabric = payload["flow_fabric"]
        expected_fields = [
            "adaptive_connections_active",
            "links_count",
            "adaptation_enabled_links",
            "total_sends",
            "total_throttled",
            "throttle_rate",
            "status",
            "contracts_tracked",
        ]
        for field in expected_fields:
            assert field in flow_fabric, f"Missing flow fabric field: {field}"

    def test_flow_fabric_metrics_collection(self):
        from nova.orchestrator.adaptive_connections import adaptive_link_registry

        metrics = adaptive_link_registry.get_all_metrics()
        assert isinstance(metrics, list)
        if metrics:
            for m in metrics:
                assert isinstance(m, dict)
                assert "contract_name" in m
                assert "adaptation_enabled" in m


class TestFlowFabricAdaptiveConnections:
    """Adaptive connections behavior."""

    def test_adaptive_link_registry_singleton(self):
        from nova.orchestrator.adaptive_connections import adaptive_link_registry
        from nova.orchestrator.adaptive_connections import adaptive_link_registry as registry2

        assert adaptive_link_registry is registry2

    def test_adaptive_connection_configuration(self):
        from nova.orchestrator.adaptive_connections import AdaptiveLinkConfig

        cfg = AdaptiveLinkConfig(
            base_weight=1.0,
            base_frequency=1.0,
            min_weight=0.1,
            max_weight=3.0,
            adaptation_enabled=True,
        )
        assert cfg.base_weight == 1.0
        assert cfg.adaptation_enabled is True
        assert cfg.min_weight == 0.1
        assert cfg.max_weight == 3.0

    def test_adaptive_link_creation(self):
        from nova.orchestrator.adaptive_connections import adaptive_link_registry, AdaptiveLinkConfig

        cfg = AdaptiveLinkConfig(base_weight=1.0, base_frequency=1.0, adaptation_enabled=False)
        link = adaptive_link_registry.get_link("TEST_CONTRACT@1", cfg)

        assert link is not None
        assert hasattr(link, "send")


class TestFlowHealthSummary:
    def test_flow_health_summary(self):
        from nova.orchestrator.flow_metrics import FlowMetrics

        flow_metrics = FlowMetrics()
        summary = flow_metrics.get_flow_health_summary()
        assert isinstance(summary, dict)
        for key in ("adaptive_connections_active", "links_count", "status"):
            assert key in summary
        assert summary["status"] in ("healthy", "degraded", "no_links")


class TestFlowFabricEnvironmentFlags:
    """Environment flag handling."""

    def test_flow_metrics_environment_flag(self):
        with patch.dict(os.environ, {"NOVA_FLOW_METRICS_ENABLED": "0"}):
            from nova.orchestrator.flow_fabric_init import initialize_flow_fabric
            try:
                initialize_flow_fabric()
            except Exception as e:  # pragma: no cover - defensive
                pytest.fail(f"Failed with metrics disabled: {e}")

    def test_adaptive_connections_environment_flag(self):
        with patch.dict(os.environ, {"NOVA_ADAPTIVE_CONNECTIONS_ENABLED": "1"}):
            from nova.orchestrator.flow_fabric_init import initialize_flow_fabric
            try:
                initialize_flow_fabric()
            except Exception as e:  # pragma: no cover - defensive
                pytest.fail(f"Failed with adaptive connections enabled: {e}")


class TestFlowFabricErrorHandling:
    def test_missing_config_file_handling(self):
        from nova.orchestrator.flow_fabric_init import load_adaptive_links_config

        cfg = load_adaptive_links_config()
        assert isinstance(cfg, dict)

    def test_flow_fabric_graceful_failure(self):
        from nova.orchestrator.flow_fabric_init import initialize_flow_fabric

        with patch("nova.orchestrator.flow_fabric_init.adaptive_link_registry") as mock_registry:
            mock_registry.get_link.side_effect = Exception("Test error")
            try:
                initialize_flow_fabric()
            except Exception as e:  # pragma: no cover - defensive
                pytest.fail(f"Flow fabric should fail gracefully: {e}")

    def test_health_reporting_without_flow_fabric(self):
        from nova.orchestrator.health import health_payload
        from nova.orchestrator.core.performance_monitor import PerformanceMonitor
        from nova.orchestrator.core import create_router

        monitor = PerformanceMonitor()
        router = create_router(monitor)
        slot_registry = {}

        payload = health_payload(slot_registry, monitor, router, None)
        assert isinstance(payload, dict)
        assert "flow_fabric" in payload


class TestFlowFabricConfigurationValidation:
    """Configuration validation + edge cases."""

    def test_contract_name_validation(self):
        from nova.orchestrator.flow_fabric_init import KNOWN_CONTRACTS

        for c in KNOWN_CONTRACTS:
            assert "@" in c
            name, version = c.split("@")
            assert name
            assert version.isdigit()

    def test_configuration_merging(self):
        from nova.orchestrator.flow_fabric_init import create_adaptive_link_config

        data = {
            "adaptive_connections_enabled": True,
            "default_config": {"base_weight": 1.0, "base_frequency": 1.0, "min_weight": 0.1},
            "contracts": {"TEST_CONTRACT@1": {"base_weight": 2.0, "priority": "high"}},
        }
        cfg = create_adaptive_link_config("TEST_CONTRACT@1", data)
        assert cfg.base_weight == 2.0   # override
        assert cfg.min_weight == 0.1    # default

    def test_empty_configuration_handling(self):
        from nova.orchestrator.flow_fabric_init import create_adaptive_link_config

        cfg = create_adaptive_link_config("TEST@1", {})
        assert cfg.base_weight == 1.0
        assert cfg.adaptation_enabled is False  # default disabled
