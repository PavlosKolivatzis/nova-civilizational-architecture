"""Integration tests for Slot09 Distortion Protection with ORP sensitivity - Phase 11.3 Step 4"""

import pytest
from unittest.mock import patch
from src.nova.slots.slot09_distortion_protection.hybrid_api import (
    HybridApiConfig,
    HybridDistortionDetectionAPI,
    apply_orp_sensitivity_to_config,
)


@pytest.fixture
def base_config():
    """Create base HybridApiConfig instance."""
    return HybridApiConfig()


# ---------- Flag Gating Tests ----------


def test_sensitivity_scaling_disabled_no_changes(base_config, monkeypatch):
    """Test NOVA_ENABLE_SLOT09_SENSITIVITY=0 does not apply scaling."""
    monkeypatch.setenv("NOVA_ENABLE_SLOT09_SENSITIVITY", "0")

    # Mock regime ledger to return heightened regime
    with patch("src.nova.slots.slot09_distortion_protection.hybrid_api._get_regime_duration") as mock_regime:
        mock_regime.return_value = {"regime": "heightened", "duration_s": 400.0}

        scaled_config = apply_orp_sensitivity_to_config(base_config)

        # Should be unchanged (no ORP scaling applied)
        assert scaled_config.ids_stability_threshold_low == base_config.ids_stability_threshold_low
        assert scaled_config.ids_stability_threshold_medium == base_config.ids_stability_threshold_medium
        assert scaled_config.ids_stability_threshold_high == base_config.ids_stability_threshold_high
        assert scaled_config.ids_drift_threshold_low == base_config.ids_drift_threshold_low


def test_sensitivity_scaling_enabled_applies_orp_scaling(base_config, monkeypatch):
    """Test NOVA_ENABLE_SLOT09_SENSITIVITY=1 applies ORP scaling."""
    monkeypatch.setenv("NOVA_ENABLE_SLOT09_SENSITIVITY", "1")
    monkeypatch.setenv("NOVA_ENABLE_REGIME_LEDGER", "1")

    # Mock regime ledger to return heightened ≥5min (multiplier=1.15)
    with patch("src.nova.slots.slot09_distortion_protection.hybrid_api._get_regime_duration") as mock_regime:
        mock_regime.return_value = {"regime": "heightened", "duration_s": 400.0}

        scaled_config = apply_orp_sensitivity_to_config(base_config)

        # Should apply ORP scaling: base * 1.15
        # ids_stability_threshold_low: 0.25 * 1.15 = 0.2875
        assert scaled_config.ids_stability_threshold_low == pytest.approx(0.2875, abs=0.001)
        # ids_stability_threshold_medium: 0.5 * 1.15 = 0.575
        assert scaled_config.ids_stability_threshold_medium == pytest.approx(0.575, abs=0.001)
        # ids_stability_threshold_high: 0.75 * 1.15 = 0.8625
        assert scaled_config.ids_stability_threshold_high == pytest.approx(0.8625, abs=0.001)


# ---------- Regime Scaling Tests ----------


def test_sensitivity_scaling_normal_regime_no_change(base_config, monkeypatch):
    """Test normal regime preserves thresholds (multiplier=1.0)."""
    monkeypatch.setenv("NOVA_ENABLE_SLOT09_SENSITIVITY", "1")
    monkeypatch.setenv("NOVA_ENABLE_REGIME_LEDGER", "1")

    with patch("src.nova.slots.slot09_distortion_protection.hybrid_api._get_regime_duration") as mock_regime:
        mock_regime.return_value = {"regime": "normal", "duration_s": 100.0}

        scaled_config = apply_orp_sensitivity_to_config(base_config)

        # Normal regime: no scaling (multiplier=1.0)
        assert scaled_config.ids_stability_threshold_low == base_config.ids_stability_threshold_low
        assert scaled_config.ids_drift_threshold_low == base_config.ids_drift_threshold_low


def test_sensitivity_scaling_heightened_short_duration(base_config, monkeypatch):
    """Test heightened <5min scales by 1.05."""
    monkeypatch.setenv("NOVA_ENABLE_SLOT09_SENSITIVITY", "1")
    monkeypatch.setenv("NOVA_ENABLE_REGIME_LEDGER", "1")

    with patch("src.nova.slots.slot09_distortion_protection.hybrid_api._get_regime_duration") as mock_regime:
        mock_regime.return_value = {"regime": "heightened", "duration_s": 100.0}

        scaled_config = apply_orp_sensitivity_to_config(base_config)

        # Heightened <5min: multiplier=1.05
        # 0.25 * 1.05 = 0.2625
        assert scaled_config.ids_stability_threshold_low == pytest.approx(0.2625, abs=0.001)


def test_sensitivity_scaling_heightened_long_duration(base_config, monkeypatch):
    """Test heightened ≥5min scales by 1.15."""
    monkeypatch.setenv("NOVA_ENABLE_SLOT09_SENSITIVITY", "1")
    monkeypatch.setenv("NOVA_ENABLE_REGIME_LEDGER", "1")

    with patch("src.nova.slots.slot09_distortion_protection.hybrid_api._get_regime_duration") as mock_regime:
        mock_regime.return_value = {"regime": "heightened", "duration_s": 400.0}

        scaled_config = apply_orp_sensitivity_to_config(base_config)

        # Heightened ≥5min: multiplier=1.15
        # 0.25 * 1.15 = 0.2875
        assert scaled_config.ids_stability_threshold_low == pytest.approx(0.2875, abs=0.001)


def test_sensitivity_scaling_emergency_regime(base_config, monkeypatch):
    """Test emergency_stabilization scales by 1.50."""
    monkeypatch.setenv("NOVA_ENABLE_SLOT09_SENSITIVITY", "1")
    monkeypatch.setenv("NOVA_ENABLE_REGIME_LEDGER", "1")

    with patch("src.nova.slots.slot09_distortion_protection.hybrid_api._get_regime_duration") as mock_regime:
        mock_regime.return_value = {"regime": "emergency_stabilization", "duration_s": 100.0}

        scaled_config = apply_orp_sensitivity_to_config(base_config)

        # Emergency: multiplier=1.50
        # 0.25 * 1.50 = 0.375
        assert scaled_config.ids_stability_threshold_low == pytest.approx(0.375, abs=0.001)


def test_sensitivity_scaling_recovery_regime(base_config, monkeypatch):
    """Test recovery scales by 1.20 (gradual recovery)."""
    monkeypatch.setenv("NOVA_ENABLE_SLOT09_SENSITIVITY", "1")
    monkeypatch.setenv("NOVA_ENABLE_REGIME_LEDGER", "1")

    with patch("src.nova.slots.slot09_distortion_protection.hybrid_api._get_regime_duration") as mock_regime:
        mock_regime.return_value = {"regime": "recovery", "duration_s": 500.0}

        scaled_config = apply_orp_sensitivity_to_config(base_config)

        # Recovery: multiplier=1.20
        # 0.25 * 1.20 = 0.30
        assert scaled_config.ids_stability_threshold_low == pytest.approx(0.30, abs=0.001)


# ---------- API Integration Tests ----------


def test_hybrid_api_applies_sensitivity_scaling_on_init(monkeypatch):
    """Test HybridDistortionDetectionAPI applies sensitivity scaling on initialization."""
    monkeypatch.setenv("NOVA_ENABLE_SLOT09_SENSITIVITY", "1")
    monkeypatch.setenv("NOVA_ENABLE_REGIME_LEDGER", "1")

    with patch("src.nova.slots.slot09_distortion_protection.hybrid_api._get_regime_duration") as mock_regime:
        mock_regime.return_value = {"regime": "heightened", "duration_s": 400.0}

        base_config = HybridApiConfig()
        api = HybridDistortionDetectionAPI(config=base_config)

        # Verify config was scaled during __init__
        # 0.25 * 1.15 = 0.2875
        assert api.config.ids_stability_threshold_low == pytest.approx(0.2875, abs=0.001)


def test_hybrid_api_no_scaling_when_disabled(monkeypatch):
    """Test HybridDistortionDetectionAPI preserves config when scaling disabled."""
    monkeypatch.setenv("NOVA_ENABLE_SLOT09_SENSITIVITY", "0")

    base_config = HybridApiConfig()
    api = HybridDistortionDetectionAPI(config=base_config)

    # Verify config was NOT scaled
    assert api.config.ids_stability_threshold_low == base_config.ids_stability_threshold_low


# ---------- All Threshold Scaling Tests ----------


def test_all_ids_thresholds_scaled(base_config, monkeypatch):
    """Test all IDS stability and drift thresholds are scaled."""
    monkeypatch.setenv("NOVA_ENABLE_SLOT09_SENSITIVITY", "1")
    monkeypatch.setenv("NOVA_ENABLE_REGIME_LEDGER", "1")

    with patch("src.nova.slots.slot09_distortion_protection.hybrid_api._get_regime_duration") as mock_regime:
        mock_regime.return_value = {"regime": "heightened", "duration_s": 400.0}

        scaled_config = apply_orp_sensitivity_to_config(base_config)

        # Verify ALL stability thresholds scaled
        assert scaled_config.ids_stability_threshold_low > base_config.ids_stability_threshold_low
        assert scaled_config.ids_stability_threshold_medium > base_config.ids_stability_threshold_medium
        assert scaled_config.ids_stability_threshold_high > base_config.ids_stability_threshold_high

        # Verify ALL drift thresholds scaled
        assert scaled_config.ids_drift_threshold_low > base_config.ids_drift_threshold_low
        assert scaled_config.ids_drift_threshold_medium > base_config.ids_drift_threshold_medium
        assert scaled_config.ids_drift_threshold_high > base_config.ids_drift_threshold_high


def test_threat_thresholds_not_scaled(base_config, monkeypatch):
    """Test threat_threshold_* are NOT scaled (response thresholds, not detection)."""
    monkeypatch.setenv("NOVA_ENABLE_SLOT09_SENSITIVITY", "1")
    monkeypatch.setenv("NOVA_ENABLE_REGIME_LEDGER", "1")

    with patch("src.nova.slots.slot09_distortion_protection.hybrid_api._get_regime_duration") as mock_regime:
        mock_regime.return_value = {"regime": "emergency_stabilization", "duration_s": 100.0}

        scaled_config = apply_orp_sensitivity_to_config(base_config)

        # Threat thresholds should be unchanged (these are response thresholds)
        assert scaled_config.threat_threshold_warning == base_config.threat_threshold_warning
        assert scaled_config.threat_threshold_block == base_config.threat_threshold_block


def test_resilience_settings_not_scaled(base_config, monkeypatch):
    """Test resilience settings are NOT scaled."""
    monkeypatch.setenv("NOVA_ENABLE_SLOT09_SENSITIVITY", "1")
    monkeypatch.setenv("NOVA_ENABLE_REGIME_LEDGER", "1")

    with patch("src.nova.slots.slot09_distortion_protection.hybrid_api._get_regime_duration") as mock_regime:
        mock_regime.return_value = {"regime": "emergency_stabilization", "duration_s": 100.0}

        scaled_config = apply_orp_sensitivity_to_config(base_config)

        # Resilience settings should be unchanged
        assert scaled_config.max_content_length_bytes == base_config.max_content_length_bytes
        assert scaled_config.circuit_breaker_threshold == base_config.circuit_breaker_threshold
        assert scaled_config.cache_ttl_seconds == base_config.cache_ttl_seconds


# ---------- Constraint Tests ----------


def test_sensitivity_scaling_increases_thresholds(base_config, monkeypatch):
    """Test scaling increases thresholds (reduces sensitivity)."""
    monkeypatch.setenv("NOVA_ENABLE_SLOT09_SENSITIVITY", "1")
    monkeypatch.setenv("NOVA_ENABLE_REGIME_LEDGER", "1")

    with patch("src.nova.slots.slot09_distortion_protection.hybrid_api._get_regime_duration") as mock_regime:
        # All non-normal regimes have multipliers > 1.0
        mock_regime.return_value = {"regime": "heightened", "duration_s": 400.0}

        scaled_config = apply_orp_sensitivity_to_config(base_config)

        # All thresholds should be higher (less sensitive)
        assert scaled_config.ids_stability_threshold_low > base_config.ids_stability_threshold_low
        assert scaled_config.ids_drift_threshold_low > base_config.ids_drift_threshold_low


def test_sensitivity_scaling_bounded_to_2x(base_config, monkeypatch):
    """Test scaled thresholds never exceed 2x base (safety bound)."""
    monkeypatch.setenv("NOVA_ENABLE_SLOT09_SENSITIVITY", "1")
    monkeypatch.setenv("NOVA_ENABLE_REGIME_LEDGER", "1")

    with patch("src.nova.slots.slot09_distortion_protection.hybrid_api._get_regime_duration") as mock_regime:
        # Emergency has highest multiplier (1.50)
        mock_regime.return_value = {"regime": "emergency_stabilization", "duration_s": 100.0}

        scaled_config = apply_orp_sensitivity_to_config(base_config)

        # Verify all thresholds ≤ 2x base
        assert scaled_config.ids_stability_threshold_low <= base_config.ids_stability_threshold_low * 2.0
        assert scaled_config.ids_drift_threshold_low <= base_config.ids_drift_threshold_low * 2.0


def test_sensitivity_scaling_multiplicative_not_additive(base_config, monkeypatch):
    """Test scaling is multiplicative (threshold * multiplier)."""
    monkeypatch.setenv("NOVA_ENABLE_SLOT09_SENSITIVITY", "1")
    monkeypatch.setenv("NOVA_ENABLE_REGIME_LEDGER", "1")

    with patch("src.nova.slots.slot09_distortion_protection.hybrid_api._get_regime_duration") as mock_regime:
        mock_regime.return_value = {"regime": "heightened", "duration_s": 400.0}

        scaled_config = apply_orp_sensitivity_to_config(base_config)

        # Multiplicative: 0.25 * 1.15 = 0.2875
        # NOT additive: 0.25 + 1.15 = 1.40
        assert scaled_config.ids_stability_threshold_low == pytest.approx(0.2875, abs=0.001)
        assert scaled_config.ids_stability_threshold_low != pytest.approx(1.40, abs=0.001)


# ---------- Exception Handling Tests ----------


def test_sensitivity_scaling_fallback_on_exception(base_config, monkeypatch):
    """Test fallback to base config if ORP scaling raises exception."""
    monkeypatch.setenv("NOVA_ENABLE_SLOT09_SENSITIVITY", "1")
    monkeypatch.setenv("NOVA_ENABLE_REGIME_LEDGER", "1")

    with patch("src.nova.slots.slot09_distortion_protection.hybrid_api._get_regime_duration") as mock_regime:
        # Simulate exception in ledger
        mock_regime.side_effect = Exception("Ledger failed")

        scaled_config = apply_orp_sensitivity_to_config(base_config)

        # Should fallback to base config (graceful degradation)
        assert scaled_config.ids_stability_threshold_low == base_config.ids_stability_threshold_low
        assert scaled_config.ids_drift_threshold_low == base_config.ids_drift_threshold_low


def test_sensitivity_scaling_graceful_when_imports_fail(base_config, monkeypatch):
    """Test graceful behavior when imports fail (fallback stubs)."""
    monkeypatch.setenv("NOVA_ENABLE_SLOT09_SENSITIVITY", "1")

    # This test verifies the try/except import fallback stubs work
    # If imports failed, apply_orp_sensitivity_to_config returns base config unchanged
    scaled_config = apply_orp_sensitivity_to_config(base_config)

    # Should return valid config (imports work in test env)
    assert isinstance(scaled_config, HybridApiConfig)
    assert scaled_config.ids_stability_threshold_low >= 0.0


# ---------- Edge Cases ----------


def test_sensitivity_scaling_interpretation():
    """Test correct interpretation: higher multiplier = less sensitive = higher threshold."""
    monkeypatch_instance = pytest.MonkeyPatch()
    monkeypatch_instance.setenv("NOVA_ENABLE_SLOT09_SENSITIVITY", "1")
    monkeypatch_instance.setenv("NOVA_ENABLE_REGIME_LEDGER", "1")

    base_config = HybridApiConfig()

    with patch("src.nova.slots.slot09_distortion_protection.hybrid_api._get_regime_duration") as mock_regime:
        # Normal: baseline sensitivity
        mock_regime.return_value = {"regime": "normal", "duration_s": 100.0}
        normal_config = apply_orp_sensitivity_to_config(base_config)

        # Emergency: reduced sensitivity (higher threshold)
        mock_regime.return_value = {"regime": "emergency_stabilization", "duration_s": 100.0}
        emergency_config = apply_orp_sensitivity_to_config(base_config)

        # Emergency should have higher threshold (less sensitive)
        assert emergency_config.ids_stability_threshold_low > normal_config.ids_stability_threshold_low
        # Emergency detects only more severe cases (stability < 0.375 vs < 0.25)

    monkeypatch_instance.undo()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
