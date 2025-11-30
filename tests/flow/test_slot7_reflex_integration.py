"""
Tests for Slot 7 Reflex Integration with Flow Fabric

Validates reflex emission, hysteresis, clamp bounds, and upstream link modulation.
"""
import pytest
import time
from unittest.mock import patch

from nova.orchestrator.reflex_signals import ReflexBus, ReflexSignal, setup_slot7_reflex_integration
from nova.orchestrator.adaptive_connections import AdaptiveLink, AdaptiveLinkConfig, adaptive_link_registry
from nova.slots.slot07_production_controls.reflex_emitter import (
    ReflexEmitter, ReflexPolicyManager, get_reflex_emitter, reset_reflex_emitter
)
from nova.slots.slot07_production_controls.production_control_engine import ProductionControlEngine


class TestSlot7ReflexIntegration:
    """Test reflex emission from Slot 7 to adaptive links."""

    def setup_method(self):
        """Setup for each test"""
        # Reset global state
        reset_reflex_emitter()
        adaptive_link_registry.links.clear()

        # Create test policy
        self.test_policy = {
            "reflex_policy": {
                "enabled": True,
                "shadow_mode": False,  # Actually emit for testing
                "max_emission_rate": 10.0,  # High rate for testing
                "smoothing_alpha": 0.2,
                "debounce_window_seconds": 1.0
            },
            "signals": {
                "breaker_pressure": {
                    "hysteresis": {"rise_threshold": 0.8, "fall_threshold": 0.6},
                    "cooldown_seconds": 1.0,
                    "clamps": {
                        "min_frequency_multiplier": 0.3,
                        "max_frequency_multiplier": 1.0,
                        "min_weight_multiplier": 0.5,
                        "max_weight_multiplier": 1.0
                    }
                },
                "memory_pressure": {
                    "hysteresis": {"rise_threshold": 0.85, "fall_threshold": 0.7},
                    "cooldown_seconds": 1.0,
                    "clamps": {
                        "min_frequency_multiplier": 0.2,
                        "max_frequency_multiplier": 1.0,
                        "min_weight_multiplier": 0.3,
                        "max_weight_multiplier": 1.0
                    }
                }
            }
        }

        # Create reflex emitter with test policy
        self.policy_manager = ReflexPolicyManager()
        self.policy_manager.policy = self.test_policy

        # Create reflex bus
        self.reflex_bus = ReflexBus()

        # Create reflex emitter
        self.reflex_emitter = ReflexEmitter(self.reflex_bus.emit_reflex, self.policy_manager)

    def test_circuit_breaker_emits_reflex(self):
        """Test that circuit breaker pressure emits reflex signal"""
        # Setup - should emit when pressure > 0.8 (rise threshold)
        trace_id = f"test_{int(time.time() * 1000)}"

        # Emit breaker pressure signal above threshold
        result = self.reflex_emitter.emit_breaker_pressure(
            circuit_state="half-open",
            raw_pressure=0.85,
            cause="circuit_breaker_pressure_test",
            trace_id=trace_id
        )

        assert result is True, "Should emit signal when pressure above rise threshold"

        # Check metrics tracking
        metrics = self.reflex_emitter.get_metrics()
        assert metrics["signals_emitted_by_type"]["breaker_pressure"] == 1
        assert "breaker_pressure" in metrics["active_signal_states"]
        assert metrics["active_signal_states"]["breaker_pressure"] is True

        # Check ledger entry
        recent_ledger = self.reflex_emitter.get_recent_ledger(limit=1)
        assert len(recent_ledger) == 1
        entry = recent_ledger[0]
        assert entry.signal_type == "breaker_pressure"
        assert entry.trace_id == trace_id
        assert entry.emission_allowed is True
        assert 0.3 <= entry.clamped_pressure <= 1.0  # Within clamp bounds

    def test_reflex_adjusts_upstream_links(self):
        """Test that reflex signals adjust S3→S6 adaptive link frequencies"""
        # Setup - register EMOTION_REPORT@1 adaptive link
        link_config = AdaptiveLinkConfig(adaptation_enabled=True)
        emotion_link = AdaptiveLink("EMOTION_REPORT@1", link_config)

        # Register with reflex bus
        self.reflex_bus.register_adaptive_link("EMOTION_REPORT@1", emotion_link)

        # Record original values
        original_frequency = emotion_link.frequency
        original_weight = emotion_link.weight

        # Create high pressure reflex signal
        reflex_signal = ReflexSignal(
            signal_type="breaker_pressure",
            source_slot="slot07_production_controls",
            pressure_level=0.9,  # High pressure
            cause="test_pressure",
            timestamp=time.time(),
            trace_id="test_trace",
            clamps={
                "min_frequency_multiplier": 0.3,
                "max_frequency_multiplier": 1.0,
                "min_weight_multiplier": 0.5,
                "max_weight_multiplier": 1.0
            },
            metadata={"circuit_state": "open"}
        )

        # Emit reflex signal
        self.reflex_bus.emit_reflex(reflex_signal)

        # Check that adaptive link was adjusted
        assert emotion_link.frequency < original_frequency, "Frequency should be reduced under pressure"
        assert emotion_link.frequency >= 0.3, "Frequency should respect minimum clamp"
        assert emotion_link.weight <= original_weight, "Weight should be reduced or same"
        assert emotion_link.weight >= 0.5, "Weight should respect minimum clamp"

        # Check adjustment reasons
        assert emotion_link.metrics.frequency_adjustments > 0
        assert emotion_link.metrics.weight_adjustments > 0

    def test_hysteresis_prevents_oscillation(self):
        """Test hysteresis prevents rapid on/off oscillation"""
        # Clear state for clean test
        self.reflex_emitter.signal_states.clear()
        self.reflex_emitter.last_emissions.clear()

        # Start with pressure above rise threshold (0.8)
        self.reflex_emitter.emit_breaker_pressure("open", 0.85, "initial_pressure")
        assert self.reflex_emitter.signal_states["breaker_pressure"] is True

        # Drop pressure below rise threshold but above fall threshold (0.6)
        # Should stay active due to hysteresis
        time.sleep(1.1)  # Wait past cooldown to allow state update
        self.reflex_emitter.emit_breaker_pressure("half-open", 0.75, "mid_pressure")
        assert self.reflex_emitter.signal_states["breaker_pressure"] is True

        # Drop pressure below fall threshold (0.6) - should deactivate
        time.sleep(1.1)  # Wait past cooldown
        self.reflex_emitter.emit_breaker_pressure("closed", 0.55, "low_pressure")
        assert self.reflex_emitter.signal_states["breaker_pressure"] is False

    def test_cooldown_prevents_spam(self):
        """Test cooldown prevents rapid signal emission"""
        # Emit first signal
        result1 = self.reflex_emitter.emit_breaker_pressure("open", 0.9, "first_signal")
        assert result1 is True

        # Immediately emit second signal (should be blocked by cooldown)
        result2 = self.reflex_emitter.emit_breaker_pressure("open", 0.95, "second_signal")
        assert result2 is False, "Second signal should be blocked by cooldown"

        # Check ledger shows cooldown blocking
        recent_ledger = self.reflex_emitter.get_recent_ledger(limit=2)
        assert len(recent_ledger) == 2
        assert recent_ledger[1].emission_allowed is False
        assert recent_ledger[1].cooldown_remaining > 0.0

    def test_rate_limiting(self):
        """Test global rate limiting prevents system overload"""
        # Set very low rate limit for testing (0.1/sec over 60s window = max 6 emissions)
        self.policy_manager.policy["reflex_policy"]["max_emission_rate"] = 0.1  # 0.1 per second

        # Saturate the rate limit by setting emissions_in_window to max
        self.reflex_emitter.emissions_in_window = 6  # 0.1 * 60 = 6 max emissions

        # Reset cooldown state to test rate limiting specifically
        self.reflex_emitter.last_emissions.clear()

        # This emission should be blocked by rate limit
        result = self.reflex_emitter.emit_memory_pressure(10, 5, 2, "rate_limited")
        assert result is False, "Should be blocked by global rate limit"

    def test_memory_pressure_signal(self):
        """Test memory pressure signal emission and processing"""
        # Setup cultural profile link
        link_config = AdaptiveLinkConfig(adaptation_enabled=True)
        cultural_link = AdaptiveLink("CULTURAL_PROFILE@1", link_config)
        self.reflex_bus.register_adaptive_link("CULTURAL_PROFILE@1", cultural_link)

        # Clear any previous emissions to avoid rate limiting
        self.reflex_emitter.last_emissions.clear()
        self.reflex_emitter.emissions_in_window = 0

        # Emit memory pressure with high values to trigger emission
        result = self.reflex_emitter.emit_memory_pressure(
            active_requests=95,  # Very high utilization
            max_requests=100,
            resource_violations=8,  # High violation count
            cause="resource_exhaustion"
        )

        assert result is True

        # Check that cultural synthesis was throttled more aggressively
        assert cultural_link.frequency < 1.0, "Cultural synthesis should be throttled under memory pressure"
        assert cultural_link.frequency >= 0.2, "Should respect minimum clamp"


class TestReflexPolicyManager:
    """Test reflex policy management and configuration"""

    def test_policy_loading_with_environment_override(self):
        """Test policy loading with environment-specific overrides"""
        with patch.dict('os.environ', {'NOVA_CURRENT_MODE': 'development'}):
            policy_manager = ReflexPolicyManager()

            # Should have development overrides applied
            assert policy_manager.is_emission_enabled() is True  # Dev override
            assert policy_manager.is_shadow_mode() is False      # Dev override

    def test_feature_flag_overrides(self):
        """Test feature flag environment variable overrides"""
        with patch.dict('os.environ', {
            'NOVA_REFLEX_ENABLED': '1',
            'NOVA_REFLEX_SHADOW': '0'
        }):
            policy_manager = ReflexPolicyManager()

            assert policy_manager.is_emission_enabled() is True
            assert policy_manager.is_shadow_mode() is False


@pytest.mark.integration
class TestFullReflexIntegration:
    """Integration tests for complete reflex flow"""

    def test_production_engine_to_adaptive_link_integration(self):
        """Test complete flow from production engine through reflex to adaptive link"""
        # Setup complete integration
        adaptive_link_registry.links.clear()

        # Create and register adaptive link
        link_config = AdaptiveLinkConfig(adaptation_enabled=True)
        emotion_link = AdaptiveLink("EMOTION_REPORT@1", link_config)
        adaptive_link_registry.links["EMOTION_REPORT@1"] = emotion_link

        # Setup reflex integration
        setup_slot7_reflex_integration()

        # Create production engine
        ProductionControlEngine()

        # Get reflex emitter (should be wired to bus now)
        reflex_emitter = get_reflex_emitter()
        reflex_emitter.policy_manager.policy["reflex_policy"]["enabled"] = True
        reflex_emitter.policy_manager.policy["reflex_policy"]["shadow_mode"] = False

        # Trigger circuit breaker by causing failures
        original_frequency = emotion_link.frequency

        # Simulate high circuit breaker pressure
        reflex_emitter.emit_breaker_pressure("open", 0.9, "integration_test")

        # Check that S3→S6 link was adjusted
        assert emotion_link.frequency < original_frequency
        assert emotion_link.frequency >= 0.3  # Respects clamps

        # Verify metrics were updated
        metrics = reflex_emitter.get_metrics()
        assert metrics["signals_emitted_by_type"]["breaker_pressure"] > 0
