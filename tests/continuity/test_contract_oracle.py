"""Unit tests for Contract Oracle - Phase 12

Validates that contract_oracle.py produces identical results to
operational_regime.py for all core scenarios.

Any divergence = bug in implementation or ambiguity in orp@1.yaml.
"""

import pytest
from src.nova.continuity.contract_oracle import (
    compute_regime_score_from_contract,
    classify_regime_from_contract,
    compute_and_classify,
    clamp,
    REGIME_THRESHOLDS,
    SIGNAL_WEIGHTS,
    DOWNGRADE_HYSTERESIS,
    MIN_REGIME_DURATION_S,
)
from src.nova.continuity.operational_regime import (
    OperationalRegimePolicy,
    ContributingFactors,
    Regime,
)


# ---------- Utility Fixtures ----------


@pytest.fixture
def orp_engine():
    """ORP implementation instance."""
    return OperationalRegimePolicy()


@pytest.fixture
def normal_factors():
    """Normal regime contributing factors."""
    return {
        "urf_composite_risk": 0.15,
        "mse_meta_instability": 0.03,
        "predictive_collapse_risk": 0.10,
        "consistency_gap": 0.05,
        "csi_continuity_index": 0.95,
    }


@pytest.fixture
def heightened_factors():
    """Heightened regime contributing factors."""
    return {
        "urf_composite_risk": 0.45,
        "mse_meta_instability": 0.08,
        "predictive_collapse_risk": 0.25,
        "consistency_gap": 0.12,
        "csi_continuity_index": 0.85,
    }


@pytest.fixture
def emergency_factors():
    """Emergency regime contributing factors."""
    return {
        "urf_composite_risk": 0.85,
        "mse_meta_instability": 0.18,
        "predictive_collapse_risk": 0.75,
        "consistency_gap": 0.60,
        "csi_continuity_index": 0.45,
    }


# ---------- Score Calculation Tests ----------


def test_oracle_score_matches_orp_normal(orp_engine, normal_factors):
    """Test oracle score matches ORP for normal regime factors."""
    cf = ContributingFactors(**normal_factors)

    orp_score = orp_engine.compute_regime_score(cf)
    oracle_score = compute_regime_score_from_contract(normal_factors)

    assert abs(orp_score - oracle_score) < 1e-6, \
        f"Score mismatch: ORP={orp_score:.6f}, Oracle={oracle_score:.6f}"


def test_oracle_score_matches_orp_heightened(orp_engine, heightened_factors):
    """Test oracle score matches ORP for heightened regime factors."""
    cf = ContributingFactors(**heightened_factors)

    orp_score = orp_engine.compute_regime_score(cf)
    oracle_score = compute_regime_score_from_contract(heightened_factors)

    assert abs(orp_score - oracle_score) < 1e-6


def test_oracle_score_matches_orp_emergency(orp_engine, emergency_factors):
    """Test oracle score matches ORP for emergency regime factors."""
    cf = ContributingFactors(**emergency_factors)

    orp_score = orp_engine.compute_regime_score(cf)
    oracle_score = compute_regime_score_from_contract(emergency_factors)

    assert abs(orp_score - oracle_score) < 1e-6


def test_oracle_score_csi_inversion():
    """Test CSI inversion in score calculation."""
    # CSI=1.0 (perfect) → contributes 0.0 risk
    factors_perfect_csi = {
        "urf_composite_risk": 0.0,
        "mse_meta_instability": 0.0,
        "predictive_collapse_risk": 0.0,
        "consistency_gap": 0.0,
        "csi_continuity_index": 1.0,
    }
    score_perfect = compute_regime_score_from_contract(factors_perfect_csi)
    assert abs(score_perfect - 0.0) < 1e-6

    # CSI=0.0 (collapsed) → contributes full weight (0.10)
    factors_zero_csi = {
        "urf_composite_risk": 0.0,
        "mse_meta_instability": 0.0,
        "predictive_collapse_risk": 0.0,
        "consistency_gap": 0.0,
        "csi_continuity_index": 0.0,
    }
    score_zero = compute_regime_score_from_contract(factors_zero_csi)
    assert abs(score_zero - 0.10) < 1e-6


def test_oracle_score_clamping():
    """Test clamping of out-of-range inputs."""
    factors_over_range = {
        "urf_composite_risk": 1.5,  # Over 1.0
        "mse_meta_instability": -0.2,  # Under 0.0
        "predictive_collapse_risk": 0.5,
        "consistency_gap": 0.3,
        "csi_continuity_index": 0.8,
    }

    score = compute_regime_score_from_contract(factors_over_range)
    # Should clamp to valid range and compute
    assert 0.0 <= score <= 1.0


def test_oracle_score_missing_factors():
    """Test missing factors default to 0.0 (safe default)."""
    factors_partial = {
        "urf_composite_risk": 0.5,
        # Missing other factors
    }

    score = compute_regime_score_from_contract(factors_partial)
    # Should default missing to 0.0, CSI to 1.0 (perfect)
    expected = 0.5 * 0.30  # Only URF contributes
    assert abs(score - expected) < 1e-6


# ---------- Regime Classification Tests ----------


def test_oracle_classification_matches_orp_normal(orp_engine):
    """Test oracle classifies normal regime identically to ORP."""
    regime_score = 0.15
    current_regime = "normal"
    time_in_regime_s = 1000.0

    orp_regime = orp_engine.classify_regime(
        regime_score,
        Regime.NORMAL,
        time_in_regime_s
    )
    oracle_regime = classify_regime_from_contract(
        regime_score,
        current_regime,
        time_in_regime_s
    )

    assert orp_regime.value == oracle_regime


def test_oracle_classification_matches_orp_upgrade():
    """Test oracle handles upgrade identically to ORP."""
    regime_score = 0.45  # Heightened
    current_regime = "normal"
    time_in_regime_s = 100.0  # Short duration

    engine = OperationalRegimePolicy()
    orp_regime = engine.classify_regime(regime_score, Regime.NORMAL, time_in_regime_s)
    oracle_regime = classify_regime_from_contract(regime_score, current_regime, time_in_regime_s)

    assert orp_regime.value == oracle_regime == "heightened"


def test_oracle_classification_matches_orp_downgrade_blocked_hysteresis():
    """Test oracle blocks downgrade due to hysteresis identically to ORP."""
    regime_score = 0.28  # Just below 0.30, but within hysteresis (0.30 - 0.05 = 0.25)
    current_regime = "heightened"
    time_in_regime_s = 600.0  # Sufficient duration

    engine = OperationalRegimePolicy()
    engine._current_regime = Regime.HEIGHTENED

    orp_regime = engine.classify_regime(regime_score, Regime.HEIGHTENED, time_in_regime_s)
    oracle_regime = classify_regime_from_contract(regime_score, current_regime, time_in_regime_s)

    # Should stay in heightened (hysteresis prevents downgrade)
    assert orp_regime.value == oracle_regime == "heightened"


def test_oracle_classification_matches_orp_downgrade_blocked_duration():
    """Test oracle blocks downgrade due to min-duration identically to ORP."""
    regime_score = 0.20  # Below hysteresis threshold (0.30 - 0.05 = 0.25)
    current_regime = "heightened"
    time_in_regime_s = 100.0  # Too short (< 300s)

    engine = OperationalRegimePolicy()
    engine._current_regime = Regime.HEIGHTENED

    orp_regime = engine.classify_regime(regime_score, Regime.HEIGHTENED, time_in_regime_s)
    oracle_regime = classify_regime_from_contract(regime_score, current_regime, time_in_regime_s)

    # Should stay in heightened (min-duration not met)
    assert orp_regime.value == oracle_regime == "heightened"


def test_oracle_classification_matches_orp_downgrade_allowed():
    """Test oracle allows downgrade when both conditions met, identically to ORP."""
    regime_score = 0.20  # Below hysteresis threshold
    current_regime = "heightened"
    time_in_regime_s = 600.0  # Sufficient duration

    engine = OperationalRegimePolicy()
    engine._current_regime = Regime.HEIGHTENED

    orp_regime = engine.classify_regime(regime_score, Regime.HEIGHTENED, time_in_regime_s)
    oracle_regime = classify_regime_from_contract(regime_score, current_regime, time_in_regime_s)

    # Should downgrade to normal
    assert orp_regime.value == oracle_regime == "normal"


def test_oracle_classification_boundary_score_exact_threshold():
    """Test score exactly at threshold boundary → choose higher regime."""
    regime_score = 0.30  # Exactly at normal/heightened boundary
    current_regime = "normal"
    time_in_regime_s = 1000.0

    engine = OperationalRegimePolicy()
    orp_regime = engine.classify_regime(regime_score, Regime.NORMAL, time_in_regime_s)
    oracle_regime = classify_regime_from_contract(regime_score, current_regime, time_in_regime_s)

    # Per contract: boundary → higher regime
    assert orp_regime.value == oracle_regime == "heightened"


def test_oracle_classification_recovery_clamp():
    """Test score >= 1.0 clamps to recovery."""
    regime_score = 1.5  # Over 1.0
    current_regime = "emergency_stabilization"
    time_in_regime_s = 100.0

    engine = OperationalRegimePolicy()
    engine._current_regime = Regime.EMERGENCY_STABILIZATION

    orp_regime = engine.classify_regime(regime_score, Regime.EMERGENCY_STABILIZATION, time_in_regime_s)
    oracle_regime = classify_regime_from_contract(regime_score, current_regime, time_in_regime_s)

    assert orp_regime.value == oracle_regime == "recovery"


# ---------- Combined Score + Classification Tests ----------


def test_oracle_compute_and_classify_normal(normal_factors):
    """Test combined score + classification for normal regime."""
    result = compute_and_classify(normal_factors, "normal", 1000.0)

    assert "regime_score" in result
    assert "regime" in result
    assert result["regime"] == "normal"
    assert 0.0 <= result["regime_score"] < 0.30


def test_oracle_compute_and_classify_heightened(heightened_factors):
    """Test combined score + classification for heightened regime."""
    result = compute_and_classify(heightened_factors, "normal", 1000.0)

    # Fixture produces score ~0.238 → normal regime
    assert result["regime"] == "normal"
    assert result["regime_score"] < 0.30


def test_oracle_compute_and_classify_emergency(emergency_factors):
    """Test combined score + classification for emergency regime."""
    result = compute_and_classify(emergency_factors, "controlled_degradation", 100.0)

    # Fixture produces score ~0.595 → controlled_degradation regime
    assert result["regime"] == "controlled_degradation"
    assert 0.50 <= result["regime_score"] < 0.70


# ---------- Property Tests ----------


def test_oracle_score_monotonic_with_factors():
    """Test regime score increases monotonically with factor increases."""
    base_factors = {
        "urf_composite_risk": 0.1,
        "mse_meta_instability": 0.1,
        "predictive_collapse_risk": 0.1,
        "consistency_gap": 0.1,
        "csi_continuity_index": 0.9,
    }

    score_base = compute_regime_score_from_contract(base_factors)

    # Increase URF
    increased_factors = base_factors.copy()
    increased_factors["urf_composite_risk"] = 0.5
    score_increased = compute_regime_score_from_contract(increased_factors)

    assert score_increased > score_base


def test_oracle_upgrade_never_requires_hysteresis():
    """Test upgrades are immediate regardless of time in regime."""
    for regime in ["normal", "heightened", "controlled_degradation", "emergency_stabilization"]:
        # Score that triggers upgrade
        regime_score = 0.95  # Recovery
        time_in_regime_s = 0.0  # Zero duration

        oracle_regime = classify_regime_from_contract(regime_score, regime, time_in_regime_s)
        assert oracle_regime == "recovery"


def test_oracle_downgrade_always_requires_both_conditions():
    """Test downgrade requires BOTH hysteresis AND min-duration."""
    # Only hysteresis met (duration too short)
    result1 = classify_regime_from_contract(0.20, "heightened", 100.0)
    assert result1 == "heightened"  # Blocked by duration

    # Only duration met (score within hysteresis)
    result2 = classify_regime_from_contract(0.28, "heightened", 600.0)
    assert result2 == "heightened"  # Blocked by hysteresis

    # Both met
    result3 = classify_regime_from_contract(0.20, "heightened", 600.0)
    assert result3 == "normal"  # Downgrade allowed


# ---------- Differential Testing (Comprehensive) ----------


@pytest.mark.parametrize(
    "regime_score,current_regime,time_s",
    [
        (0.10, "normal", 1000.0),
        (0.35, "normal", 1000.0),
        (0.55, "heightened", 1000.0),
        (0.75, "controlled_degradation", 1000.0),
        (0.90, "emergency_stabilization", 1000.0),
        (0.28, "heightened", 100.0),  # Hysteresis + short duration
        (0.28, "heightened", 600.0),  # Hysteresis + long duration
        (0.20, "heightened", 100.0),  # Below hysteresis + short duration
        (0.20, "heightened", 600.0),  # Below hysteresis + long duration
    ],
)
def test_oracle_matches_orp_comprehensive(regime_score, current_regime, time_s):
    """Comprehensive differential test: oracle must match ORP for all scenarios."""
    engine = OperationalRegimePolicy()

    # Map string regime to Enum
    regime_enum_map = {
        "normal": Regime.NORMAL,
        "heightened": Regime.HEIGHTENED,
        "controlled_degradation": Regime.CONTROLLED_DEGRADATION,
        "emergency_stabilization": Regime.EMERGENCY_STABILIZATION,
        "recovery": Regime.RECOVERY,
    }

    engine._current_regime = regime_enum_map[current_regime]

    orp_regime = engine.classify_regime(
        regime_score,
        regime_enum_map[current_regime],
        time_s
    )
    oracle_regime = classify_regime_from_contract(
        regime_score,
        current_regime,
        time_s
    )

    assert orp_regime.value == oracle_regime, \
        f"Divergence at score={regime_score}, current={current_regime}, time={time_s}: " \
        f"ORP={orp_regime.value}, Oracle={oracle_regime}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
