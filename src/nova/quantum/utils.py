"""Utility helpers for Nova quantum circuits."""

from __future__ import annotations

try:
    import cirq
except Exception:  # pragma: no cover - optional dependency
    cirq = None  # type: ignore


def make_hadamard_measure_circuit(n_qubits: int = 1, key: str = "r"):
    """Build a simple Hadamard + measurement circuit."""
    if cirq is None:
        raise RuntimeError("Cirq is not available to build circuits")

    qubits = cirq.LineQubit.range(max(1, n_qubits))
    circuit = cirq.Circuit()
    circuit.append(cirq.H.on_each(*qubits))
    circuit.append(cirq.measure(*qubits, key=key))
    return circuit


def circuit_to_json(circuit) -> str:
    """Serialize a Cirq circuit to JSON."""
    if cirq is None:
        raise RuntimeError("Cirq is not available to serialize circuits")
    return cirq.to_json(circuit)


__all__ = ["make_hadamard_measure_circuit", "circuit_to_json"]
