"""Test Slot03 phase-lock publishing to Semantic Mirror."""

import pytest
from unittest.mock import patch
from slots.slot03_emotional_matrix.publish import publish_phase_lock_to_mirror


class MockMirror:
    def __init__(self):
        self.contexts = {}

    def set_context(self, key, value, ttl=None):
        self.contexts[key] = value


def test_publish_phase_lock_success():
    """Test successful phase-lock publishing to mirror."""
    mock_mirror = MockMirror()

    with patch('orchestrator.semantic_mirror.get_semantic_mirror', return_value=mock_mirror):
        publish_phase_lock_to_mirror(0.52)

    assert mock_mirror.contexts['slot03.phase_lock'] == 0.52


def test_publish_phase_lock_none_value():
    """Test handling of None value (should not publish)."""
    mock_mirror = MockMirror()

    with patch('orchestrator.semantic_mirror.get_semantic_mirror', return_value=mock_mirror):
        publish_phase_lock_to_mirror(None)

    assert len(mock_mirror.contexts) == 0


def test_publish_phase_lock_import_error():
    """Test graceful handling when semantic mirror not available."""
    with patch('orchestrator.semantic_mirror.get_semantic_mirror', side_effect=ImportError("Mock import error")):
        # Should not raise exception
        publish_phase_lock_to_mirror(0.48)


def test_publish_phase_lock_set_context_error():
    """Test graceful handling when mirror.set_context fails."""
    mock_mirror = MockMirror()
    mock_mirror.set_context = lambda key, value, ttl=None: (_ for _ in ()).throw(Exception("Mock set_context error"))

    with patch('orchestrator.semantic_mirror.get_semantic_mirror', return_value=mock_mirror):
        # Should not raise exception
        publish_phase_lock_to_mirror(0.55)


def test_publish_phase_lock_fallback_signature():
    """Test fallback to set_context without ttl when TypeError occurs."""
    class MockMirrorNoTTL:
        def __init__(self):
            self.contexts = {}

        def set_context(self, key, value):  # No ttl parameter
            self.contexts[key] = value

    mock_mirror = MockMirrorNoTTL()

    # Mock the function to first raise TypeError, then succeed
    original_set_context = mock_mirror.set_context

    def mock_set_context_with_ttl(key, value, ttl=None):
        if ttl is not None:
            raise TypeError("Unexpected keyword argument 'ttl'")
        return original_set_context(key, value)

    mock_mirror.set_context = mock_set_context_with_ttl

    with patch('orchestrator.semantic_mirror.get_semantic_mirror', return_value=mock_mirror):
        publish_phase_lock_to_mirror(0.47)

    assert mock_mirror.contexts['slot03.phase_lock'] == 0.47