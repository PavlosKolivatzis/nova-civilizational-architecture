"""
Slot03 Emotional Matrix VOID Dormancy Tests

Phase 14.4: RFC-014 § 3.2 compliance.
Tests that empty content with graph_state='void' maps to dormancy, not negative affect.
"""

import pytest
from src.nova.slots.slot03_emotional_matrix.emotional_matrix_engine import EmotionalMatrixEngine


def test_void_dormancy_with_context():
    """Empty content with graph_state='void' → dormant, not unknown"""
    engine = EmotionalMatrixEngine()

    result = engine.analyze("", context={"graph_state": "void"})

    assert result["emotional_tone"] == "dormant"
    assert result["score"] is None  # Null, not 0.0
    assert result["confidence"] == 1.0  # VOID is fully defined
    assert result["explain"]["void_dormancy"] is True
    assert result["explain"]["graph_state"] == "void"


def test_void_dormancy_metric_increments():
    """VOID dormancy increments metric"""
    from src.nova.slots.slot03_emotional_matrix.emotional_matrix_engine import _void_dormancy_counter

    # Check if metric is accessible (may be DummyCounter)
    if hasattr(_void_dormancy_counter, '_value'):
        initial = _void_dormancy_counter._value._value

        engine = EmotionalMatrixEngine()
        engine.analyze("", context={"graph_state": "void"})

        assert _void_dormancy_counter._value._value == initial + 1


def test_empty_content_without_void_context_legacy():
    """Empty content without VOID context → unknown (legacy behavior)"""
    engine = EmotionalMatrixEngine()

    result = engine.analyze("")  # No context

    assert result["emotional_tone"] == "unknown"
    assert result["score"] == 0.0
    assert result["confidence"] == 0.0
    assert "void_dormancy" not in result["explain"]


def test_empty_content_with_non_void_context():
    """Empty content with graph_state='normal' → unknown (no dormancy)"""
    engine = EmotionalMatrixEngine()

    result = engine.analyze("", context={"graph_state": "normal"})

    assert result["emotional_tone"] == "unknown"
    assert result["score"] == 0.0
    assert result["confidence"] == 0.0


def test_void_dormancy_flag_disabled(monkeypatch):
    """NOVA_ENABLE_VOID_MODE=0 → no dormancy (legacy behavior)"""
    monkeypatch.setenv("NOVA_ENABLE_VOID_MODE", "0")

    engine = EmotionalMatrixEngine()
    result = engine.analyze("", context={"graph_state": "void"})

    assert result["emotional_tone"] == "unknown"  # Not "dormant"
    assert result["score"] == 0.0
    assert result["confidence"] == 0.0


def test_non_empty_content_unaffected_by_void_context():
    """Non-empty content with VOID context → normal sentiment analysis"""
    engine = EmotionalMatrixEngine()

    result = engine.analyze("This is great!", context={"graph_state": "void"})

    # Should analyze sentiment normally (VOID context only for empty content)
    assert result["emotional_tone"] != "dormant"
    assert result["score"] != 0.0  # Positive sentiment detected
    assert "void_dormancy" not in result["explain"]


def test_void_dormancy_avoids_negative_affect():
    """VOID dormancy produces neutral/null affect, not fear/compliance"""
    engine = EmotionalMatrixEngine()

    result = engine.analyze("", context={"graph_state": "void"})

    # RFC-014 § 3.2: avoid ["fear", "compliance", "safety signals"]
    assert result["emotional_tone"] not in ["fear", "compliance", "negative"]
    assert result["emotional_tone"] == "dormant"
    assert result["score"] is None  # Null, not negative
