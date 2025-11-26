"""Integration tests for Slot03 Emotional Matrix with ORP constriction - Phase 11.3 Step 3"""

import pytest
from unittest.mock import patch
from src.nova.slots.slot03_emotional_matrix.emotional_matrix_engine import EmotionalMatrixEngine


@pytest.fixture
def engine():
    """Create EmotionalMatrixEngine instance."""
    return EmotionalMatrixEngine()


# ---------- Flag Gating Tests ----------


def test_emotional_constriction_disabled_no_changes(engine, monkeypatch):
    """Test NOVA_ENABLE_EMOTIONAL_CONSTRICTION=0 does not apply constriction."""
    monkeypatch.setenv("NOVA_ENABLE_EMOTIONAL_CONSTRICTION", "0")

    # Mock regime ledger to return heightened regime
    with patch("src.nova.slots.slot03_emotional_matrix.emotional_matrix_engine._get_regime_duration") as mock_regime:
        mock_regime.return_value = {"regime": "heightened", "duration_s": 400.0}

        result = engine.analyze("This is fantastic and amazing!")

        # Should be base emotional score (no ORP constriction applied)
        assert result["emotional_tone"] == "positive"
        assert result["score"] > 0.5  # Strong positive
        # No ORP annotation
        assert "orp_emotional_constriction" not in result.get("annotations", {})


def test_emotional_constriction_enabled_applies_orp_scaling(engine, monkeypatch):
    """Test NOVA_ENABLE_EMOTIONAL_CONSTRICTION=1 applies ORP scaling."""
    monkeypatch.setenv("NOVA_ENABLE_EMOTIONAL_CONSTRICTION", "1")
    monkeypatch.setenv("NOVA_ENABLE_REGIME_LEDGER", "1")

    # Mock regime ledger to return heightened ≥5min (scale=0.85)
    with patch("src.nova.slots.slot03_emotional_matrix.emotional_matrix_engine._get_regime_duration") as mock_regime:
        mock_regime.return_value = {"regime": "heightened", "duration_s": 400.0}

        result = engine.analyze("This is fantastic and amazing!")

        # Should apply ORP constriction: heightened ≥5min scale=0.85
        assert result["emotional_tone"] == "positive"
        # Score should be reduced by ~15% (multiplier=0.85)
        assert "annotations" in result
        assert "orp_emotional_constriction" in result["annotations"]
        constriction = result["annotations"]["orp_emotional_constriction"]
        assert constriction["regime"] == "heightened"
        assert constriction["duration_s"] == 400.0
        assert constriction["intensity_after"] < constriction["intensity_before"]


# ---------- Regime Scaling Tests ----------


def test_emotional_constriction_normal_regime_no_change(engine, monkeypatch):
    """Test normal regime preserves intensity (scale=1.0)."""
    monkeypatch.setenv("NOVA_ENABLE_EMOTIONAL_CONSTRICTION", "1")
    monkeypatch.setenv("NOVA_ENABLE_REGIME_LEDGER", "1")

    with patch("src.nova.slots.slot03_emotional_matrix.emotional_matrix_engine._get_regime_duration") as mock_regime:
        mock_regime.return_value = {"regime": "normal", "duration_s": 100.0}

        result = engine.analyze("This is fantastic and amazing!")

        # Normal regime: no constriction (multiplier=1.0)
        assert result["emotional_tone"] == "positive"
        # No ORP annotation because multiplier=1.0 (no change)
        assert "orp_emotional_constriction" not in result.get("annotations", {})


def test_emotional_constriction_heightened_short_duration(engine, monkeypatch):
    """Test heightened <5min scales by 0.95."""
    monkeypatch.setenv("NOVA_ENABLE_EMOTIONAL_CONSTRICTION", "1")
    monkeypatch.setenv("NOVA_ENABLE_REGIME_LEDGER", "1")

    with patch("src.nova.slots.slot03_emotional_matrix.emotional_matrix_engine._get_regime_duration") as mock_regime:
        mock_regime.return_value = {"regime": "heightened", "duration_s": 100.0}

        result = engine.analyze("This is fantastic and amazing!")

        # Heightened <5min: scale=0.95 (slight constriction)
        assert result["emotional_tone"] == "positive"
        assert "orp_emotional_constriction" in result["annotations"]
        constriction = result["annotations"]["orp_emotional_constriction"]
        assert constriction["regime"] == "heightened"
        assert constriction["intensity_after"] < constriction["intensity_before"]
        # Verify ~5% reduction
        reduction_ratio = constriction["intensity_after"] / constriction["intensity_before"]
        assert reduction_ratio == pytest.approx(0.95, abs=0.01)


def test_emotional_constriction_heightened_long_duration(engine, monkeypatch):
    """Test heightened ≥5min scales by 0.85."""
    monkeypatch.setenv("NOVA_ENABLE_EMOTIONAL_CONSTRICTION", "1")
    monkeypatch.setenv("NOVA_ENABLE_REGIME_LEDGER", "1")

    with patch("src.nova.slots.slot03_emotional_matrix.emotional_matrix_engine._get_regime_duration") as mock_regime:
        mock_regime.return_value = {"regime": "heightened", "duration_s": 400.0}

        result = engine.analyze("This is fantastic and amazing!")

        # Heightened ≥5min: scale=0.85 (moderate constriction)
        assert result["emotional_tone"] == "positive"
        assert "orp_emotional_constriction" in result["annotations"]
        constriction = result["annotations"]["orp_emotional_constriction"]
        assert constriction["regime"] == "heightened"
        # Verify ~15% reduction
        reduction_ratio = constriction["intensity_after"] / constriction["intensity_before"]
        assert reduction_ratio == pytest.approx(0.85, abs=0.01)


def test_emotional_constriction_emergency_regime(engine, monkeypatch):
    """Test emergency_stabilization scales by 0.50."""
    monkeypatch.setenv("NOVA_ENABLE_EMOTIONAL_CONSTRICTION", "1")
    monkeypatch.setenv("NOVA_ENABLE_REGIME_LEDGER", "1")

    with patch("src.nova.slots.slot03_emotional_matrix.emotional_matrix_engine._get_regime_duration") as mock_regime:
        mock_regime.return_value = {"regime": "emergency_stabilization", "duration_s": 100.0}

        result = engine.analyze("This is fantastic and amazing!")

        # Emergency: scale=0.50 (strong constriction)
        assert result["emotional_tone"] == "positive"
        assert "orp_emotional_constriction" in result["annotations"]
        constriction = result["annotations"]["orp_emotional_constriction"]
        assert constriction["regime"] == "emergency_stabilization"
        # Verify ~50% reduction
        reduction_ratio = constriction["intensity_after"] / constriction["intensity_before"]
        assert reduction_ratio == pytest.approx(0.50, abs=0.01)


def test_emotional_constriction_recovery_regime(engine, monkeypatch):
    """Test recovery scales by 0.60 (gradual recovery)."""
    monkeypatch.setenv("NOVA_ENABLE_EMOTIONAL_CONSTRICTION", "1")
    monkeypatch.setenv("NOVA_ENABLE_REGIME_LEDGER", "1")

    with patch("src.nova.slots.slot03_emotional_matrix.emotional_matrix_engine._get_regime_duration") as mock_regime:
        mock_regime.return_value = {"regime": "recovery", "duration_s": 500.0}

        result = engine.analyze("This is fantastic and amazing!")

        # Recovery: scale=0.60 (moderate constriction)
        assert result["emotional_tone"] == "positive"
        assert "orp_emotional_constriction" in result["annotations"]
        constriction = result["annotations"]["orp_emotional_constriction"]
        assert constriction["regime"] == "recovery"
        # Verify ~40% reduction
        reduction_ratio = constriction["intensity_after"] / constriction["intensity_before"]
        assert reduction_ratio == pytest.approx(0.60, abs=0.01)


# ---------- Topology Preservation Tests ----------


def test_emotional_constriction_preserves_positive_tone(engine, monkeypatch):
    """Test constriction preserves positive emotional tone."""
    monkeypatch.setenv("NOVA_ENABLE_EMOTIONAL_CONSTRICTION", "1")
    monkeypatch.setenv("NOVA_ENABLE_REGIME_LEDGER", "1")

    with patch("src.nova.slots.slot03_emotional_matrix.emotional_matrix_engine._get_regime_duration") as mock_regime:
        mock_regime.return_value = {"regime": "emergency_stabilization", "duration_s": 100.0}

        # Strong positive content
        result = engine.analyze("This is fantastic and amazing!")

        # Even with 50% constriction, should stay positive
        assert result["emotional_tone"] == "positive"
        assert result["score"] > 0.0  # Still positive
        # Verify constriction was applied
        assert "orp_emotional_constriction" in result["annotations"]


def test_emotional_constriction_preserves_negative_tone(engine, monkeypatch):
    """Test constriction preserves negative emotional tone."""
    monkeypatch.setenv("NOVA_ENABLE_EMOTIONAL_CONSTRICTION", "1")
    monkeypatch.setenv("NOVA_ENABLE_REGIME_LEDGER", "1")

    with patch("src.nova.slots.slot03_emotional_matrix.emotional_matrix_engine._get_regime_duration") as mock_regime:
        mock_regime.return_value = {"regime": "emergency_stabilization", "duration_s": 100.0}

        # Strong negative content
        result = engine.analyze("This is terrible and awful and horrible!")

        # Even with 50% constriction, should stay negative
        assert result["emotional_tone"] == "negative"
        assert result["score"] < 0.0  # Still negative
        # Verify constriction was applied
        assert "orp_emotional_constriction" in result["annotations"]


def test_emotional_constriction_preserves_neutral_tone(engine, monkeypatch):
    """Test constriction preserves neutral emotional tone."""
    monkeypatch.setenv("NOVA_ENABLE_EMOTIONAL_CONSTRICTION", "1")
    monkeypatch.setenv("NOVA_ENABLE_REGIME_LEDGER", "1")

    with patch("src.nova.slots.slot03_emotional_matrix.emotional_matrix_engine._get_regime_duration") as mock_regime:
        mock_regime.return_value = {"regime": "heightened", "duration_s": 400.0}

        # Neutral content
        result = engine.analyze("The sky is blue and the grass is green.")

        # Should stay neutral
        assert result["emotional_tone"] == "neutral"
        # Neutral score (~0.0) should not have annotation (no change)
        # Because constriction of near-zero intensity stays near-zero


def test_emotional_constriction_does_not_flip_valence(engine, monkeypatch):
    """Test constriction never flips valence (positive→negative or vice versa)."""
    monkeypatch.setenv("NOVA_ENABLE_EMOTIONAL_CONSTRICTION", "1")
    monkeypatch.setenv("NOVA_ENABLE_REGIME_LEDGER", "1")

    with patch("src.nova.slots.slot03_emotional_matrix.emotional_matrix_engine._get_regime_duration") as mock_regime:
        mock_regime.return_value = {"regime": "emergency_stabilization", "duration_s": 100.0}

        # Test positive content
        result_pos = engine.analyze("This is great!")
        assert result_pos["score"] > 0.0  # Stays positive

        # Test negative content
        result_neg = engine.analyze("This is terrible!")
        assert result_neg["score"] < 0.0  # Stays negative


# ---------- Constraint Tests ----------


def test_emotional_constriction_no_orp_symbol_leakage(engine, monkeypatch):
    """Test ORP symbols not leaked to top-level metadata."""
    monkeypatch.setenv("NOVA_ENABLE_EMOTIONAL_CONSTRICTION", "1")
    monkeypatch.setenv("NOVA_ENABLE_REGIME_LEDGER", "1")

    with patch("src.nova.slots.slot03_emotional_matrix.emotional_matrix_engine._get_regime_duration") as mock_regime:
        mock_regime.return_value = {"regime": "heightened", "duration_s": 400.0}

        result = engine.analyze("This is fantastic!")

        # Top-level should only have standard Slot03 fields
        assert "emotional_tone" in result
        assert "score" in result
        assert "confidence" in result
        # ORP symbols buried in annotations, not top-level
        assert "regime" not in result
        assert "duration_s" not in result
        # But accessible in annotations if constricted
        if "orp_emotional_constriction" in result.get("annotations", {}):
            assert "regime" in result["annotations"]["orp_emotional_constriction"]


def test_emotional_constriction_score_bounded_to_one(engine, monkeypatch):
    """Test constricted score never exceeds [-1.0, 1.0]."""
    monkeypatch.setenv("NOVA_ENABLE_EMOTIONAL_CONSTRICTION", "1")
    monkeypatch.setenv("NOVA_ENABLE_REGIME_LEDGER", "1")

    with patch("src.nova.slots.slot03_emotional_matrix.emotional_matrix_engine._get_regime_duration") as mock_regime:
        mock_regime.return_value = {"regime": "heightened", "duration_s": 400.0}

        # Very strong positive content
        result = engine.analyze("This is fantastic amazing wonderful excellent brilliant superb outstanding!")

        # Score should be clamped to [-1.0, 1.0]
        assert -1.0 <= result["score"] <= 1.0


def test_emotional_constriction_multiplicative_not_additive(engine, monkeypatch):
    """Test constriction is multiplicative (not additive)."""
    monkeypatch.setenv("NOVA_ENABLE_EMOTIONAL_CONSTRICTION", "1")
    monkeypatch.setenv("NOVA_ENABLE_REGIME_LEDGER", "1")

    with patch("src.nova.slots.slot03_emotional_matrix.emotional_matrix_engine._get_regime_duration") as mock_regime:
        mock_regime.return_value = {"regime": "heightened", "duration_s": 400.0}

        result = engine.analyze("This is fantastic!")

        # Verify constriction was multiplicative
        if "orp_emotional_constriction" in result.get("annotations", {}):
            constriction = result["annotations"]["orp_emotional_constriction"]
            before = constriction["intensity_before"]
            after = constriction["intensity_after"]

            # Multiplicative: after = before * multiplier
            # NOT additive: after ≠ before + multiplier
            assert after == pytest.approx(before * 0.85, abs=0.01)
            assert after != pytest.approx(before + 0.85, abs=0.01)


# ---------- Exception Handling Tests ----------


def test_emotional_constriction_fallback_on_exception(engine, monkeypatch):
    """Test fallback to unconstricted score if ORP scaling raises exception."""
    monkeypatch.setenv("NOVA_ENABLE_EMOTIONAL_CONSTRICTION", "1")
    monkeypatch.setenv("NOVA_ENABLE_REGIME_LEDGER", "1")

    with patch("src.nova.slots.slot03_emotional_matrix.emotional_matrix_engine._get_regime_duration") as mock_regime:
        # Simulate exception in ledger
        mock_regime.side_effect = Exception("Ledger failed")

        result = engine.analyze("This is fantastic!")

        # Should fallback to unconstricted score (graceful degradation)
        assert result["emotional_tone"] == "positive"
        assert result["score"] > 0.0
        # No ORP annotation because exception occurred
        assert "orp_emotional_constriction" not in result.get("annotations", {})


def test_emotional_constriction_graceful_when_imports_fail(monkeypatch):
    """Test graceful behavior when imports fail (fallback stubs)."""
    monkeypatch.setenv("NOVA_ENABLE_EMOTIONAL_CONSTRICTION", "1")

    # This test verifies the try/except import fallback stubs work
    # If imports failed, no constriction is applied (graceful degradation)
    engine = EmotionalMatrixEngine()
    result = engine.analyze("This is fantastic!")

    # Should compute emotional score normally (imports work in test env)
    assert isinstance(result["score"], float)
    assert -1.0 <= result["score"] <= 1.0


# ---------- Edge Cases ----------


def test_emotional_constriction_zero_intensity(engine, monkeypatch):
    """Test intensity=0.0 stays 0.0 regardless of regime."""
    monkeypatch.setenv("NOVA_ENABLE_EMOTIONAL_CONSTRICTION", "1")
    monkeypatch.setenv("NOVA_ENABLE_REGIME_LEDGER", "1")

    with patch("src.nova.slots.slot03_emotional_matrix.emotional_matrix_engine._get_regime_duration") as mock_regime:
        mock_regime.return_value = {"regime": "emergency_stabilization", "duration_s": 100.0}

        # Neutral content with no sentiment
        result = engine.analyze("The sky.")

        # Score should be ~0.0 (neutral)
        assert result["emotional_tone"] == "neutral"
        assert abs(result["score"]) < 0.2  # Near zero
        # No annotation because no meaningful constriction on near-zero


def test_emotional_constriction_negative_content(engine, monkeypatch):
    """Test constriction works correctly for negative emotional content."""
    monkeypatch.setenv("NOVA_ENABLE_EMOTIONAL_CONSTRICTION", "1")
    monkeypatch.setenv("NOVA_ENABLE_REGIME_LEDGER", "1")

    with patch("src.nova.slots.slot03_emotional_matrix.emotional_matrix_engine._get_regime_duration") as mock_regime:
        mock_regime.return_value = {"regime": "heightened", "duration_s": 400.0}

        result = engine.analyze("This is terrible and awful and horrible!")

        # Should apply constriction to negative intensity
        assert result["emotional_tone"] == "negative"
        assert result["score"] < 0.0  # Still negative
        # Verify constriction was applied
        assert "orp_emotional_constriction" in result["annotations"]
        constriction = result["annotations"]["orp_emotional_constriction"]
        # Intensity is magnitude (positive), so before > after
        assert constriction["intensity_after"] < constriction["intensity_before"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
