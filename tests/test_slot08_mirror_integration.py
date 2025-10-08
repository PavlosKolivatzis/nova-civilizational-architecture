"""Test Slot08 semantic mirror integration."""

from unittest.mock import patch
from slots.slot08_memory_lock.core.repair_planner import RepairPlanner


class MockMirror:
    def __init__(self, pressure=None, phase_coherence=None):
        self.pressure = pressure
        self.phase_coherence = phase_coherence

    def get_context(self, key, requester):
        if key == "slot07.pressure_level" and self.pressure is not None:
            return self.pressure
        if key == "slot04.phase_coherence" and self.phase_coherence is not None:
            return self.phase_coherence
        return None


def test_phase_lock_prefers_phase_coherence():
    """Test phase_lock prefers TRI phase coherence when available."""
    planner = RepairPlanner()

    with patch('orchestrator.semantic_mirror.get_semantic_mirror') as mock_get_mirror:
        mock_get_mirror.return_value = MockMirror(phase_coherence=0.82, pressure=0.9)

        phase_lock = planner._get_phase_lock()
        assert abs(phase_lock - 0.82) < 1e-9


def test_phase_lock_pressure_modulation():
    """Test phase_lock modulates based on system pressure."""
    planner = RepairPlanner()

    with patch('orchestrator.semantic_mirror.get_semantic_mirror') as mock_get_mirror:
        mock_get_mirror.return_value = MockMirror(pressure=0.8)

        phase_lock = planner._get_phase_lock()
        # High pressure (0.8) should give: 0.60 - 0.20 * 0.8 = 0.44
        assert abs(phase_lock - 0.44) < 0.01


def test_phase_lock_pressure_range():
    """Test phase_lock pressure mapping covers expected range."""
    planner = RepairPlanner()

    # Test low pressure
    with patch('orchestrator.semantic_mirror.get_semantic_mirror') as mock_get_mirror:
        mock_get_mirror.return_value = MockMirror(pressure=0.0)
        phase_lock = planner._get_phase_lock()
        assert abs(phase_lock - 0.60) < 0.01

    # Test high pressure
    with patch('orchestrator.semantic_mirror.get_semantic_mirror') as mock_get_mirror:
        mock_get_mirror.return_value = MockMirror(pressure=1.0)
        phase_lock = planner._get_phase_lock()
        assert abs(phase_lock - 0.40) < 0.01


def test_phase_lock_env_fallback():
    """Test phase_lock falls back to env var when mirror unavailable."""
    planner = RepairPlanner()

    with patch('orchestrator.semantic_mirror.get_semantic_mirror') as mock_get_mirror:
        mock_get_mirror.return_value = MockMirror()  # No data

        with patch('os.getenv') as mock_getenv:
            mock_getenv.side_effect = lambda key, default=None: "0.65" if key == "SLOT07_PHASE_LOCK" else default

            phase_lock = planner._get_phase_lock()
            assert abs(phase_lock - 0.65) < 1e-9


def test_phase_lock_default_fallback():
    """Test phase_lock uses default when all else fails."""
    planner = RepairPlanner()

    with patch('orchestrator.semantic_mirror.get_semantic_mirror', side_effect=ImportError("Mock import error")):
        phase_lock = planner._get_phase_lock()
        assert phase_lock == 0.5


def test_phase_lock_deep_disabled():
    """Test phase_lock returns None when NOVA_LIGHTCLOCK_DEEP=0."""
    planner = RepairPlanner()

    with patch('os.getenv') as mock_getenv:
        mock_getenv.side_effect = lambda key, default=None: "0" if key == "NOVA_LIGHTCLOCK_DEEP" else default

        phase_lock = planner._get_phase_lock()
        assert phase_lock is None