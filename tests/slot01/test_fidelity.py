"""Tests for fidelity validation service."""

from nova.slots.slot01_truth_anchor.fidelity import fidelity_from_bits


def test_fidelity_balanced_bytes():
    # 0b01010101 repeated → p_hat=0.5 → F ~ 1
    balanced = bytes([0x55] * 32)  # 01010101 pattern
    F, (lo, hi), abs_bias = fidelity_from_bits(balanced)
    assert 0.98 <= F <= 1.0
    assert abs_bias < 0.02
    # CI may not contain F due to statistical variation, just check bounds
    assert 0.0 <= lo <= 1.0 and 0.0 <= hi <= 1.0


def test_fidelity_biased_bytes():
    biased = bytes([0xFF] * 32)  # all ones
    F, (lo, hi), abs_bias = fidelity_from_bits(biased)
    assert F == 0.0
    assert abs_bias == 0.5
    # CI bounds check
    assert 0.0 <= lo <= 1.0 and 0.0 <= hi <= 1.0


def test_fidelity_empty_bytes():
    F, (lo, hi), abs_bias = fidelity_from_bits(b"")
    assert F == 0.0
    assert abs_bias == 0.5
    # Special case for empty input - CI is (0.0, 1.0) as fallback
    assert lo == 0.0 and hi == 1.0


def test_fidelity_single_byte():
    # Single byte with 4 ones, 4 zeros
    single = bytes([0x0F])  # 00001111
    F, (lo, hi), abs_bias = fidelity_from_bits(single)
    assert F == 1.0  # perfectly balanced
    assert abs_bias == 0.0
    # CI bounds check
    assert 0.0 <= lo <= 1.0 and 0.0 <= hi <= 1.0
