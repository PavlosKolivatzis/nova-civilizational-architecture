"""Test Slot05 TRI signal integration."""

import pytest
from unittest.mock import Mock, patch
from slots.slot05_constellation.constellation_engine import ConstellationEngine


class MockMirror:
    def __init__(self, coherence=None, phase_jitter=None):
        self.coherence = coherence
        self.phase_jitter = phase_jitter

    def get_context(self, key, requester):
        if key == "slot04.coherence" and self.coherence is not None:
            return self.coherence
        if key == "slot04.phase_jitter" and self.phase_jitter is not None:
            return self.phase_jitter
        return None


def test_tri_signals_from_mirror():
    """Test TRI signals read from semantic mirror."""
    engine = ConstellationEngine()

    with patch('orchestrator.semantic_mirror.get_semantic_mirror') as mock_get_mirror:
        mock_get_mirror.return_value = MockMirror(coherence=0.85, phase_jitter=0.12)

        signals = engine._get_tri_signals()
        assert signals is not None
        assert abs(signals["coherence"] - 0.85) < 1e-9
        assert abs(signals["phase_jitter"] - 0.12) < 1e-9


def test_tri_signals_partial_mirror_data():
    """Test TRI signals with partial mirror data."""
    engine = ConstellationEngine()

    with patch('orchestrator.semantic_mirror.get_semantic_mirror') as mock_get_mirror:
        mock_get_mirror.return_value = MockMirror(coherence=0.75)  # No phase_jitter

        signals = engine._get_tri_signals()
        assert signals is not None
        assert "coherence" in signals
        assert abs(signals["coherence"] - 0.75) < 1e-9
        assert "phase_jitter" not in signals


def test_tri_signals_env_fallback():
    """Test TRI signals fall back to env vars when mirror unavailable."""
    engine = ConstellationEngine()

    with patch('orchestrator.semantic_mirror.get_semantic_mirror') as mock_get_mirror:
        mock_get_mirror.return_value = MockMirror()  # No data

        with patch('os.getenv') as mock_getenv:
            def env_side_effect(key, default=None):
                if key == "TRI_COHERENCE":
                    return "0.92"
                elif key == "TRI_PHASE_JITTER":
                    return "0.08"
                else:
                    return default

            mock_getenv.side_effect = env_side_effect

            signals = engine._get_tri_signals()
            assert signals is not None
            assert abs(signals["coherence"] - 0.92) < 1e-9
            assert abs(signals["phase_jitter"] - 0.08) < 1e-9


def test_tri_signals_deep_disabled():
    """Test TRI signals return None when NOVA_LIGHTCLOCK_DEEP=0."""
    engine = ConstellationEngine()

    with patch('os.getenv') as mock_getenv:
        mock_getenv.side_effect = lambda key, default=None: "0" if key == "NOVA_LIGHTCLOCK_DEEP" else default

        signals = engine._get_tri_signals()
        assert signals is None


def test_tri_signals_mirror_import_error():
    """Test TRI signals gracefully handle mirror import errors."""
    engine = ConstellationEngine()

    with patch('orchestrator.semantic_mirror.get_semantic_mirror', side_effect=ImportError("Mock import error")):
        with patch('os.getenv') as mock_getenv:
            mock_getenv.side_effect = lambda key, default=None: "0.7" if key == "TRI_COHERENCE" else default

            signals = engine._get_tri_signals()
            assert signals is not None
            assert abs(signals["coherence"] - 0.7) < 1e-9