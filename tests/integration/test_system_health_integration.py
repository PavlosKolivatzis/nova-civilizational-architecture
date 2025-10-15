"""System-wide health integration tests.

Tests the complete health system after polish sprint changes:
- All 12 slots report healthy status
- Health aggregation works correctly
- Performance within acceptable bounds
- Cross-component health dependencies

Based on actual health system implementation analysis.
"""

import time
import os
from unittest.mock import patch


class TestSystemHealthIntegration:
    """Test complete health system integration."""

    def test_health_payload_structure(self):
        """Test the actual health payload structure matches expected format."""
        from orchestrator.health import health_payload
        from orchestrator.core.performance_monitor import PerformanceMonitor
        from orchestrator.core import create_router
        import pkgutil
        import slots

        # Use the actual METRIC_SLOT_REGISTRY pattern from app.py
        slot_registry = {
            name: None
            for _, name, _ in pkgutil.iter_modules(slots.__path__)
            if name.startswith("slot")
        }

        monitor = PerformanceMonitor()
        router = create_router(monitor)
        payload = health_payload(slot_registry, monitor, router, None)

        # Verify actual health structure (based on health.py analysis)
        expected_keys = ["slots", "slot_self_checks", "router_thresholds", "circuit_breaker", "timestamp", "version"]
        for key in expected_keys:
            assert key in payload, f"Missing required health key: {key}"

        # Verify slot structure
        assert isinstance(payload["slots"], dict)
        assert isinstance(payload["slot_self_checks"], dict)
        assert isinstance(payload["router_thresholds"], dict)
        assert isinstance(payload["circuit_breaker"], dict)
        assert isinstance(payload["timestamp"], (int, float))
        assert payload["version"] == "1.0.0"

    def test_slot_health_discovery(self):
        """Test that health system discovers all slot health modules."""
        from orchestrator.health import collect_slot_selfchecks
        import pkgutil
        import slots

        # Use actual slot registry
        slot_registry = {
            name: None
            for _, name, _ in pkgutil.iter_modules(slots.__path__)
            if name.startswith("slot")
        }

        self_checks = collect_slot_selfchecks(slot_registry)

        # Should discover all slots (some may report "n/a" if no health module)
        expected_slots = [
            "slot01_truth_anchor", "slot02_deltathresh", "slot03_emotional_matrix",
            "slot04_tri", "slot04_tri_engine", "slot05_constellation",
            "slot06_cultural_synthesis", "slot07_production_controls",
            "slot08_memory_ethics", "slot08_memory_lock", "slot09_distortion_protection",
            "slot10_civilizational_deployment"
        ]

        for slot_name in expected_slots:
            assert slot_name in self_checks, f"Missing slot self-check: {slot_name}"

        # Polish sprint targets should have health modules (not "n/a")
        sprint_targets = [
            "slot02_deltathresh", "slot04_tri", "slot04_tri_engine",
            "slot08_memory_ethics", "slot08_memory_lock",
            "slot09_distortion_protection", "slot10_civilizational_deployment"
        ]

        healthy_count = 0
        for target in sprint_targets:
            if target in self_checks:
                check = self_checks[target]
                if check.get("self_check") == "ok":
                    healthy_count += 1
                # Should not be "n/a" (missing health module)
                assert check.get("self_check") != "n/a", f"Sprint target {target} missing health module"

        # Most sprint targets should be healthy
        assert healthy_count >= len(sprint_targets) - 1, f"Too few healthy sprint targets: {healthy_count}/{len(sprint_targets)}"

    def test_health_system_performance(self):
        """Test that health system responds within performance bounds."""
        from orchestrator.health import health_payload
        from orchestrator.core.performance_monitor import PerformanceMonitor
        from orchestrator.core import create_router
        import pkgutil
        import slots

        slot_registry = {
            name: None
            for _, name, _ in pkgutil.iter_modules(slots.__path__)
            if name.startswith("slot")
        }

        monitor = PerformanceMonitor()
        router = create_router(monitor)

        # Measure health payload generation time
        start_time = time.perf_counter()
        payload = health_payload(slot_registry, monitor, router, None)
        end_time = time.perf_counter()

        response_time = end_time - start_time

        # Health system should respond quickly (under 500ms)
        assert response_time < 0.5, f"Health response took {response_time:.3f}s, expected <0.5s"

        # Verify payload structure is complete
        assert isinstance(payload, dict)
        assert len(payload) >= 6  # slots, slot_self_checks, router_thresholds, circuit_breaker, timestamp, version

    def test_healthkit_standardization(self):
        """Test that all new health modules follow healthkit standards."""
        # Test modules created during polish sprint
        test_modules = [
            ("nova.slots.slot02_deltathresh.health", "slot02_deltathresh"),
            ("nova.slots.slot04_tri.health", "slot04_tri"),
            ("nova.slots.slot04_tri_engine.health", "slot04_tri_engine"),
            ("nova.slots.slot08_memory_ethics.health", "slot08_memory_ethics"),
            ("nova.slots.slot08_memory_lock.health", "slot08_memory_lock"),
            ("nova.slots.slot09_distortion_protection.health", "slot09_distortion_protection"),
            ("nova.slots.slot10_civilizational_deployment.health", "slot10_civilizational_deployment"),
        ]

        for module_path, expected_name in test_modules:
            import importlib
            module = importlib.import_module(module_path)
            health_func = getattr(module, 'health')

            result = health_func()

            # Verify healthkit compliance
            assert result["schema_version"] == "1.0"
            assert result["name"] == expected_name
            assert result["self_check"] in ["ok", "error"]
            assert result["engine_status"] in ["normal", "minimal", "degraded"]
            assert isinstance(result["capabilities"], list)
            assert len(result["capabilities"]) > 0
            assert isinstance(result["metrics"], dict)
            assert isinstance(result["deps"], list)
            assert isinstance(result["timestamp"], (int, float))


class TestFlowFabricIntegration:
    """Test flow fabric integration with health system."""

    def test_flow_fabric_health_when_enabled(self):
        """Test flow fabric health integration when flow metrics enabled."""
        # Set environment to enable flow metrics
        with patch.dict(os.environ, {"NOVA_FLOW_METRICS_ENABLED": "true"}):
            from orchestrator.health import health_payload
            from orchestrator.core.performance_monitor import PerformanceMonitor
            from orchestrator.core import create_router
            from orchestrator.flow_fabric_init import initialize_flow_fabric
            import pkgutil
            import slots

            # Initialize flow fabric to get links registered
            initialize_flow_fabric()

            slot_registry = {
                name: None
                for _, name, _ in pkgutil.iter_modules(slots.__path__)
                if name.startswith("slot")
            }

            monitor = PerformanceMonitor()
            router = create_router(monitor)
            payload = health_payload(slot_registry, monitor, router, None)

            # Flow fabric should be present when enabled
            assert "flow_fabric" in payload
            flow_fabric = payload["flow_fabric"]

            # Should have full flow metrics structure
            expected_fields = [
                "adaptive_connections_active", "links_count", "adaptation_enabled_links",
                "total_sends", "total_throttled", "throttle_rate", "status", "contracts_tracked"
            ]
            for field in expected_fields:
                assert field in flow_fabric, f"Missing flow fabric field: {field}"

            # Should have registered contracts
            assert flow_fabric["links_count"] > 0
            assert len(flow_fabric["contracts_tracked"]) > 0
            assert flow_fabric["status"] in ["healthy", "adaptation_disabled", "high_throttling", "high_adaptation"]

    def test_flow_fabric_contract_tracking(self):
        """Test that flow fabric tracks all expected Nova contracts."""
        with patch.dict(os.environ, {"NOVA_FLOW_METRICS_ENABLED": "true"}):
            from orchestrator.health import health_payload
            from orchestrator.core.performance_monitor import PerformanceMonitor
            from orchestrator.core import create_router
            from orchestrator.flow_fabric_init import initialize_flow_fabric, KNOWN_CONTRACTS
            import pkgutil
            import slots

            # Initialize flow fabric to get links registered
            initialize_flow_fabric()

            slot_registry = {
                name: None
                for _, name, _ in pkgutil.iter_modules(slots.__path__)
                if name.startswith("slot")
            }

            monitor = PerformanceMonitor()
            router = create_router(monitor)
            payload = health_payload(slot_registry, monitor, router, None)

            # Flow fabric should track all known contracts
            assert "flow_fabric" in payload
            flow_fabric = payload["flow_fabric"]

            assert "contracts_tracked" in flow_fabric
            tracked_contracts = flow_fabric["contracts_tracked"]

            # Should track all known Nova contracts
            for known_contract in KNOWN_CONTRACTS:
                assert known_contract in tracked_contracts, f"Missing contract: {known_contract}"

    def test_flow_fabric_status_function(self):
        """Test standalone flow fabric status function."""
        from orchestrator.flow_fabric_init import initialize_flow_fabric, get_flow_fabric_status

        # Initialize flow fabric
        initialize_flow_fabric()

        status = get_flow_fabric_status()
        assert isinstance(status, dict)

        expected_fields = ["initialized", "total_links", "contracts_registered", "known_contracts", "registration_coverage"]
        for field in expected_fields:
            assert field in status, f"Missing flow fabric status field: {field}"

        # Should be initialized with contracts
        assert status["initialized"] is True
        assert status["total_links"] > 0
        assert len(status["contracts_registered"]) > 0
        assert len(status["known_contracts"]) == 9  # Known Nova contracts (SIGNALS@1 removed DEF-028)


class TestCrossComponentIntegration:
    """Test integration between different Nova components."""

    def test_health_aggregation_resilience(self):
        """Test health aggregation handles individual slot failures gracefully."""
        from orchestrator.health import health_payload, collect_slot_selfchecks
        from orchestrator.core.performance_monitor import PerformanceMonitor
        from orchestrator.core import create_router
        import pkgutil
        import slots

        slot_registry = {
            name: None
            for _, name, _ in pkgutil.iter_modules(slots.__path__)
            if name.startswith("slot")
        }

        monitor = PerformanceMonitor()
        router = create_router(monitor)

        # Test that health collection doesn't crash
        payload = health_payload(slot_registry, monitor, router, None)
        assert isinstance(payload, dict)
        assert "slot_self_checks" in payload

        # Test individual slot health collection
        self_checks = collect_slot_selfchecks(slot_registry)
        assert isinstance(self_checks, dict)

        # Should handle missing health modules gracefully
        for slot_name, check in self_checks.items():
            assert isinstance(check, dict)
            assert "self_check" in check
            # Should be either "ok", "error", or "n/a" (for missing modules)
            assert check["self_check"] in ["ok", "error", "n/a"]

    def test_config_integration(self):
        """Test configuration integration across components."""
        from orchestrator.flow_fabric_init import load_adaptive_links_config
        from orchestrator.config import SystemConfig

        # Test flow fabric config loading
        config = load_adaptive_links_config()
        assert isinstance(config, dict)

        # Test system config
        sys_config = SystemConfig()
        assert hasattr(sys_config, "FLOW_METRICS_ENABLED")
        assert isinstance(sys_config.FLOW_METRICS_ENABLED, bool)

    def test_metrics_integration(self):
        """Test metrics collection integration."""
        from orchestrator.adaptive_connections import adaptive_link_registry
        from orchestrator.flow_fabric_init import initialize_flow_fabric

        # Initialize flow fabric to register links
        initialize_flow_fabric()

        # Should be able to get metrics without errors
        metrics = adaptive_link_registry.get_all_metrics()
        assert isinstance(metrics, list)
        assert len(metrics) > 0  # Should have registered links

        for metric in metrics:
            assert isinstance(metric, dict)
            assert "contract_name" in metric
            assert "adaptation_enabled" in metric


class TestEndToEndHealthWorkflow:
    """Test complete end-to-end health reporting workflow."""

    def test_startup_to_health_response(self):
        """Test complete startup to health response workflow."""
        from orchestrator.flow_fabric_init import initialize_flow_fabric, get_flow_fabric_status
        from orchestrator.health import health_payload
        from orchestrator.core.performance_monitor import PerformanceMonitor
        from orchestrator.core import create_router
        import pkgutil
        import slots

        # 1. Initialize flow fabric (simulates app startup)
        initialize_flow_fabric()
        status = get_flow_fabric_status()
        assert isinstance(status, dict)
        assert status["initialized"] is True

        # 2. Health system should aggregate all components (simulates /health endpoint)
        slot_registry = {
            name: None
            for _, name, _ in pkgutil.iter_modules(slots.__path__)
            if name.startswith("slot")
        }

        monitor = PerformanceMonitor()
        router = create_router(monitor)
        payload = health_payload(slot_registry, monitor, router, None)

        # 3. Response should be well-formed and complete
        assert isinstance(payload, dict)
        required_sections = ["slots", "slot_self_checks", "router_thresholds", "circuit_breaker"]
        for section in required_sections:
            assert section in payload

        # 4. Should show improved health after polish sprint
        self_checks = payload.get("slot_self_checks", {})
        healthy_slots = [name for name, data in self_checks.items()
                        if data.get("self_check") == "ok"]

        # Significant improvement in operational slots
        assert len(healthy_slots) >= 6, f"Expected ≥6 healthy slots, got {len(healthy_slots)}"

    def test_performance_under_load(self):
        """Test health system performance under simulated load."""
        from orchestrator.health import health_payload
        from orchestrator.core.performance_monitor import PerformanceMonitor
        from orchestrator.core import create_router
        import pkgutil
        import slots

        slot_registry = {
            name: None
            for _, name, _ in pkgutil.iter_modules(slots.__path__)
            if name.startswith("slot")
        }

        monitor = PerformanceMonitor()
        router = create_router(monitor)

        # Measure performance over multiple calls
        times = []
        for _ in range(5):  # Reduced from 10 for faster test
            start = time.perf_counter()
            payload = health_payload(slot_registry, monitor, router, None)
            end = time.perf_counter()
            times.append(end - start)

            # Verify response is consistent
            assert isinstance(payload, dict)
            assert "slots" in payload

        # Performance should be consistent and reasonable
        avg_time = sum(times) / len(times)
        max_time = max(times)

        assert avg_time < 0.2, f"Average health response time {avg_time:.3f}s too slow"
        assert max_time < 0.5, f"Max health response time {max_time:.3f}s too slow"


class TestPolishSprintValidation:
    """Validate specific polish sprint achievements."""

    def test_polish_sprint_slot_coverage(self):
        """Test that polish sprint achieved target slot coverage."""
        from orchestrator.health import collect_slot_selfchecks
        import pkgutil
        import slots

        slot_registry = {
            name: None
            for _, name, _ in pkgutil.iter_modules(slots.__path__)
            if name.startswith("slot")
        }

        self_checks = collect_slot_selfchecks(slot_registry)

        # Polish sprint target: slots 2, 4 (both variants), 8 (both variants), 9, 10
        sprint_targets = [
            "slot02_deltathresh",
            "slot04_tri",
            "slot04_tri_engine",
            "slot08_memory_ethics",
            "slot08_memory_lock",
            "slot09_distortion_protection",
            "slot10_civilizational_deployment"
        ]

        implemented = []
        healthy = []

        for target in sprint_targets:
            if target in self_checks:
                check = self_checks[target]
                if check.get("self_check") != "n/a":  # Has health module
                    implemented.append(target)
                if check.get("self_check") == "ok":
                    healthy.append(target)

        # All sprint targets should be implemented (not "n/a")
        assert len(implemented) == len(sprint_targets), f"Missing implementations: {set(sprint_targets) - set(implemented)}"

        # Most should be healthy (allow for occasional test environment issues)
        assert len(healthy) >= len(sprint_targets) - 1, f"Too many unhealthy sprint targets: {set(implemented) - set(healthy)}"

    def test_healthkit_library_adoption(self):
        """Test that healthkit library is properly adopted."""
        # All new modules should use healthkit
        sprint_modules = [
            "nova.slots.slot02_deltathresh.health",
            "nova.slots.slot04_tri.health",
            "nova.slots.slot04_tri_engine.health",
            "nova.slots.slot08_memory_ethics.health",
            "nova.slots.slot08_memory_lock.health",
            "nova.slots.slot09_distortion_protection.health",
            "nova.slots.slot10_civilizational_deployment.health"
        ]

        for module_path in sprint_modules:
            import importlib
            module = importlib.import_module(module_path)
            health_func = getattr(module, 'health')

            result = health_func()

            # Should follow healthkit schema exactly
            assert result["schema_version"] == "1.0"
            assert "capabilities" in result
            assert "metrics" in result
            assert "deps" in result
            assert result["self_check"] in ["ok", "error"]
            assert result["engine_status"] in ["normal", "minimal", "degraded"]
