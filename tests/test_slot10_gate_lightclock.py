"""Test Slot10 deployment gate with LightClock integration."""

from unittest.mock import patch, Mock
from nova.slots.slot10_civilizational_deployment.core.lightclock_gatekeeper import LightClockGatekeeper, MirrorReader


class MirrorReaderHelper(MirrorReader):
    def __init__(self, **values):
        self.values = values

    def read(self, key: str, default=None):
        return self.values.get(key, default)


def test_gate_opens_under_good_signals():
    """Test gate opens with good TRI, phase_lock, and low pressure via mirror."""
    mirror = MirrorReaderHelper(
        **{"slot03.phase_lock": 0.52, "slot04.coherence": 0.75, "slot04.phase_jitter": 0.10, "slot07.pressure_level": 0.2}
    )
    gatekeeper = LightClockGatekeeper(mirror=mirror)
    result = gatekeeper.should_open_gate()
    assert result is True


def test_gate_blocks_on_low_coherence():
    """Test gate blocks when TRI coherence is too low."""
    mirror = MirrorReaderHelper(
        **{"slot03.phase_lock": 0.52, "slot04.coherence": 0.65, "slot04.phase_jitter": 0.10, "slot07.pressure_level": 0.2}
    )
    gatekeeper = LightClockGatekeeper(mirror=mirror)
    result = gatekeeper.should_open_gate()
    assert result is False


def test_gate_blocks_on_phase_lock_out_of_range():
    """Test gate blocks when phase_lock is outside acceptable range."""
    # Test too low
    mirror = MirrorReaderHelper(
        **{"slot03.phase_lock": 0.35, "slot04.coherence": 0.75, "slot04.phase_jitter": 0.10, "slot07.pressure_level": 0.2}
    )
    gatekeeper = LightClockGatekeeper(mirror=mirror)
    result = gatekeeper.should_open_gate()
    assert result is False

    # Test too high
    mirror = MirrorReaderHelper(
        **{"slot03.phase_lock": 0.75, "slot04.coherence": 0.75, "slot04.phase_jitter": 0.10, "slot07.pressure_level": 0.2}
    )
    gatekeeper = LightClockGatekeeper(mirror=mirror)
    result = gatekeeper.should_open_gate()
    assert result is False


def test_gate_uses_legacy_keys():
    """Test gate works with legacy slot07.phase_lock keys."""
    mirror = MirrorReaderHelper(
        **{"slot07.phase_lock": 0.52, "slot04.tri_score": 0.75, "slot04.phase_jitter": 0.10, "slot07.pressure_level": 0.2}
    )
    gatekeeper = LightClockGatekeeper(mirror=mirror)
    result = gatekeeper.should_open_gate()
    assert result is True


def test_gate_tightens_threshold_on_high_jitter():
    """Test gate requires higher coherence when jitter is high."""
    mirror = MirrorReaderHelper(
        **{"slot03.phase_lock": 0.52, "slot04.coherence": 0.68, "slot04.phase_jitter": 0.35, "slot07.pressure_level": 0.1}
    )
    gatekeeper = LightClockGatekeeper(mirror=mirror)
    # Should require coherence >= 0.66 + 0.05 = 0.71 due to high jitter
    result = gatekeeper.should_open_gate()
    assert result is False

    # But should pass with higher coherence
    mirror = MirrorReaderHelper(
        **{"slot03.phase_lock": 0.52, "slot04.coherence": 0.82, "slot04.phase_jitter": 0.35, "slot07.pressure_level": 0.1}
    )
    gatekeeper = LightClockGatekeeper(mirror=mirror)
    result = gatekeeper.should_open_gate()
    assert result is True


def test_gate_tightens_threshold_on_high_pressure():
    """Test gate requires higher coherence when system pressure is high."""
    mirror = MirrorReaderHelper(
        **{"slot03.phase_lock": 0.52, "slot04.coherence": 0.68, "slot04.phase_jitter": 0.10, "slot07.pressure_level": 0.9}
    )
    gatekeeper = LightClockGatekeeper(mirror=mirror)
    # Should require coherence >= 0.66 + 0.05*0.9 = 0.705 due to high pressure
    result = gatekeeper.should_open_gate()
    assert result is False


def test_gate_fallback_to_tri_adapter():
    """Test gate falls back to TRI adapter when mirror unavailable."""
    gatekeeper = LightClockGatekeeper()  # No mirror

    # Mock TRI adapter
    mock_adapter = Mock()
    mock_adapter.get_latest_report.return_value = {"coherence": 0.85, "phase_jitter": 0.12}

    with patch("orchestrator.adapters.slot4_tri.Slot4TRIAdapter", return_value=mock_adapter):
        result = gatekeeper.should_open_gate()
        assert result is True


def test_gate_conservative_defaults():
    """Test gate uses conservative defaults when all sources fail."""
    gatekeeper = LightClockGatekeeper()  # No mirror

    with patch("orchestrator.adapters.slot4_tri.Slot4TRIAdapter", side_effect=ImportError("Mock import error")):
        # Should use coherence=0.7, phase_lock=0.5
        result = gatekeeper.should_open_gate()
        # phase_lock=0.5 is within range [0.45,0.60] and coherence=0.7 > 0.66, so should pass
        assert result is True


def test_evaluate_deploy_gate_legacy_interface():
    """Test legacy evaluate_deploy_gate interface works with new signals."""
    mirror = MirrorReaderHelper(
        **{"slot07.phase_lock": 0.75, "slot04.tri_score": 0.75, "slot09.final_policy": "ALLOW_FASTPATH"}
    )
    gatekeeper = LightClockGatekeeper(mirror=mirror)
    result = gatekeeper.evaluate_deploy_gate({}, {})

    assert result.passed is True
    assert result.phase_lock_value == 0.75
    assert result.tri_score == 0.75
    assert result.coherence_level == "medium"
    assert result.lightclock_passes is True
    assert len(result.failed_conditions) == 0
