"""Unit tests for Slot01 quantum entropy helpers."""

from __future__ import annotations

import pytest

from nova.slots.slot01_truth_anchor import quantum_entropy
from nova.slots.slot01_truth_anchor.quantum_entropy import EntropySample

pytestmark = [pytest.mark.slot01, pytest.mark.quantum]


def test_entropy_length_default(monkeypatch):
    """Quantum path should return the requested number of bytes."""

    class DummySource:
        def __init__(self, backend="simulator", adapter=None):
            self.backend = backend

        def sample(self, n_bytes=32):
            return EntropySample(
                data=b"\xAA" * n_bytes,
                source="quantum",
                backend=self.backend,
                fidelity=0.99,
            )

    monkeypatch.setenv("NOVA_SLOT01_QUANTUM_ENTROPY_ENABLED", "true")
    monkeypatch.setattr(quantum_entropy, "QuantumEntropySource", DummySource)

    blob = quantum_entropy.get_entropy_bytes(32)

    assert isinstance(blob, bytes)
    assert len(blob) == 32


def test_fallback_env_seed(monkeypatch):
    """Environment seed should produce deterministic entropy."""
    monkeypatch.setenv("NOVA_SLOT01_QUANTUM_ENTROPY_ENABLED", "false")
    monkeypatch.setenv("NOVA_ENTROPY_SEED", "test-seed")

    first = quantum_entropy.get_entropy_bytes(16)
    second = quantum_entropy.get_entropy_bytes(16)

    assert len(first) == 16
    assert first == second


def test_fallback_random(monkeypatch):
    """Ensure fallback random entropy respects length."""
    monkeypatch.setenv("NOVA_SLOT01_QUANTUM_ENTROPY_ENABLED", "false")
    monkeypatch.delenv("NOVA_ENTROPY_SEED", raising=False)

    blob = quantum_entropy.get_entropy_bytes(8)
    assert isinstance(blob, bytes)
    assert len(blob) == 8


def test_quantum_entropy_simulator_path(monkeypatch):
    """Exercise the actual simulator when Cirq is available."""
    pytest.importorskip("cirq")

    monkeypatch.setenv("NOVA_SLOT01_QUANTUM_ENTROPY_ENABLED", "true")
    monkeypatch.delenv("NOVA_ENTROPY_SEED", raising=False)

    source = quantum_entropy.QuantumEntropySource(backend="simulator")
    sample = source.sample(4)

    assert sample.source == "quantum"
    assert sample.backend == "simulator"
    assert isinstance(sample.data, bytes)
    assert len(sample.data) == 4
    # Check fidelity metrics are computed
    assert sample.fidelity is not None
    assert sample.fidelity_ci is not None
    assert sample.abs_bias is not None
    assert 0.0 <= sample.fidelity <= 1.0
    ci_lo, ci_hi = sample.fidelity_ci
    assert ci_lo <= sample.fidelity <= ci_hi
    assert 0.0 <= sample.abs_bias <= 0.5


def test_fidelity_in_metadata(monkeypatch):
    """Fidelity metrics should appear in anchor metadata."""

    class DummySource:
        def __init__(self, backend="simulator", adapter=None):
            self.backend = backend

        def sample(self, n_bytes=32):
            return EntropySample(
                data=b"\xAA" * n_bytes,
                source="quantum",
                backend=self.backend,
                fidelity=0.99,
                fidelity_ci=(0.95, 1.0),
                abs_bias=0.01,
            )

    monkeypatch.setenv("NOVA_SLOT01_QUANTUM_ENTROPY_ENABLED", "true")
    monkeypatch.setattr(quantum_entropy, "QuantumEntropySource", DummySource)

    from nova.slots.slot01_truth_anchor import truth_anchor_engine
    engine = truth_anchor_engine.TruthAnchorEngine()

    # Register an anchor to trigger entropy sampling
    engine.register("test-anchor", "test-value")

    # Check metadata contains fidelity fields
    record = engine._anchors["test-anchor"]
    meta = record.metadata
    assert "quantum_fidelity" in meta
    assert "quantum_fidelity_ci" in meta
    assert "entropy_abs_bias" in meta
    assert "entropy_n_bits" in meta
    assert meta["quantum_fidelity"] == 0.99
    assert meta["quantum_fidelity_ci"] == (0.95, 1.0)
    assert meta["entropy_abs_bias"] == 0.01
    assert meta["entropy_n_bits"] == 256  # 32 bytes * 8
