"""Test Slot03 semantic mirror integration."""

from unittest.mock import patch
from slots.slot03_emotional_matrix.emotional_matrix_engine import EmotionalMatrixEngine


class MockMirror:
    def __init__(self, pressure=None, phase=None):
        self.pressure = pressure
        self.phase = phase

    def get_context(self, key, requester):
        if key == "slot04.phase_coherence" and self.phase is not None:
            return self.phase
        if key == "slot07.pressure_level" and self.pressure is not None:
            return self.pressure
        return None


def test_phase_lock_uses_phase_coherence_when_available():
    """Test phase_lock uses direct phase coherence from TRI when available."""
    engine = EmotionalMatrixEngine()

    with patch('orchestrator.semantic_mirror.get_semantic_mirror') as mock_get_mirror:
        mock_get_mirror.return_value = MockMirror(phase=0.88)

        phase_lock = engine._get_phase_lock()
        assert abs(phase_lock - 0.88) < 1e-9


def test_phase_lock_modulates_with_pressure():
    """Test phase_lock modulates based on system pressure when phase coherence unavailable."""
    engine = EmotionalMatrixEngine()

    with patch('orchestrator.semantic_mirror.get_semantic_mirror') as mock_get_mirror:
        mock_get_mirror.return_value = MockMirror(pressure=0.8)

        phase_lock = engine._get_phase_lock()
        # High pressure (0.8) should give: 0.60 - 0.15 * 0.8 = 0.48
        assert abs(phase_lock - 0.48) < 0.01


def test_phase_lock_pressure_range():
    """Test phase_lock pressure mapping covers expected range."""
    engine = EmotionalMatrixEngine()

    # Test low pressure
    with patch('orchestrator.semantic_mirror.get_semantic_mirror') as mock_get_mirror:
        mock_get_mirror.return_value = MockMirror(pressure=0.0)
        phase_lock = engine._get_phase_lock()
        assert abs(phase_lock - 0.60) < 0.01

    # Test high pressure
    with patch('orchestrator.semantic_mirror.get_semantic_mirror') as mock_get_mirror:
        mock_get_mirror.return_value = MockMirror(pressure=1.0)
        phase_lock = engine._get_phase_lock()
        assert abs(phase_lock - 0.45) < 0.01


def test_phase_lock_fallback_to_env():
    """Test phase_lock falls back to env var when mirror data unavailable."""
    engine = EmotionalMatrixEngine()

    with patch('orchestrator.semantic_mirror.get_semantic_mirror') as mock_get_mirror:
        mock_get_mirror.return_value = MockMirror()  # No data

        with patch('os.getenv') as mock_getenv:
            mock_getenv.side_effect = lambda key, default=None: "0.75" if key == "SLOT07_PHASE_LOCK" else default

            phase_lock = engine._get_phase_lock()
            assert abs(phase_lock - 0.75) < 1e-9


def test_phase_lock_import_error_fallback():
    """Test phase_lock gracefully handles semantic mirror import errors."""
    engine = EmotionalMatrixEngine()

    with patch('orchestrator.semantic_mirror.get_semantic_mirror', side_effect=ImportError("Mock import error")):
        phase_lock = engine._get_phase_lock()
        assert phase_lock == 0.5  # Hard fallback value


def test_phase_lock_deep_disabled():
    """Test phase_lock returns None when NOVA_LIGHTCLOCK_DEEP=0."""
    engine = EmotionalMatrixEngine()

    with patch('os.getenv') as mock_getenv:
        mock_getenv.side_effect = lambda key, default=None: "0" if key == "NOVA_LIGHTCLOCK_DEEP" else default

        phase_lock = engine._get_phase_lock()
        assert phase_lock is None