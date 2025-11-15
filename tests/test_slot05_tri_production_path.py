"""Test Slot05 TRI production path without mocked mirror."""

from unittest.mock import patch
from nova.slots.slot05_constellation.constellation_engine import ConstellationEngine


def test_tri_fallbacks_work_without_mocked_mirror():
    """
    Ensure that if mirror hasn't published yet, Slot05 still gets real data
    via fallback chain, and otherwise returns a sane default.
    """
    engine = ConstellationEngine()

    # Test without any mocking - should use production fallback chain
    signals = engine._get_tri_signals()

    # Should return some valid signals or conservative default
    assert signals is not None
    assert isinstance(signals, dict)
    assert "coherence" in signals
    assert 0.0 <= signals["coherence"] <= 1.0


def test_tri_signals_mirror_available():
    """Test TRI signals when mirror has published data."""
    engine = ConstellationEngine()

    # Mock mirror with published TRI data
    class MockMirror:
        def get_context(self, key, requester):
            if key == "slot04.coherence":
                return 0.85
            elif key == "slot04.phase_jitter":
                return 0.12
            return None

    with patch('orchestrator.semantic_mirror.get_semantic_mirror', return_value=MockMirror()):
        signals = engine._get_tri_signals()

        assert signals is not None
        assert signals["coherence"] == 0.85
        assert signals["phase_jitter"] == 0.12


def test_tri_signals_env_fallback():
    """Test TRI signals fall back to environment variables when mirror empty."""
    engine = ConstellationEngine()

    # Mock empty mirror
    class MockMirror:
        def get_context(self, key, requester):
            return None

    with patch('orchestrator.semantic_mirror.get_semantic_mirror', return_value=MockMirror()):
        with patch('os.getenv') as mock_getenv:
            def env_side_effect(key, default=None):
                if key == "TRI_COHERENCE":
                    return "0.75"
                elif key == "TRI_PHASE_JITTER":
                    return "0.2"
                else:
                    return default

            mock_getenv.side_effect = env_side_effect

            signals = engine._get_tri_signals()

            assert signals is not None
            assert signals["coherence"] == 0.75
            assert signals["phase_jitter"] == 0.2


def test_tri_signals_conservative_default():
    """Test TRI signals return conservative default when all sources fail."""
    engine = ConstellationEngine()

    # Mock import error for mirror
    with patch('orchestrator.semantic_mirror.get_semantic_mirror', side_effect=ImportError("Mock import error")):
        with patch('os.getenv', return_value=None):
            signals = engine._get_tri_signals()

            assert signals is not None
            assert signals["coherence"] == 0.7  # Conservative default
