"""Slot01 Quality Oracle VOID - RFC-014 § 3.2"""
import pytest
from src.nova.slots.slot01_truth_anchor.quality_oracle import QualityOracle

def test_void_abstention():
    """VOID → quality=None (epistemic abstention)"""
    oracle = QualityOracle()
    result = oracle.validate_quality("", {}, -0.5, graph_state='void')
    assert result.decision == "ACCEPT"
    assert result.metadata['void_abstention'] is True
    assert result.metadata['quality_score'] is None

def test_void_metric():
    """VOID increments metric"""
    from src.nova.slots.slot01_truth_anchor.quality_oracle import _void_abstention_counter
    initial = _void_abstention_counter._value._value
    QualityOracle().validate_quality("", {}, -0.5, graph_state='void')
    assert _void_abstention_counter._value._value == initial + 1
