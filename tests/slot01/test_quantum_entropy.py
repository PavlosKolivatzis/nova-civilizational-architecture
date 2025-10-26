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
