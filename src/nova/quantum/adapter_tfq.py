"""TensorFlow Quantum / Cirq adapter stub for entropy generation."""

from __future__ import annotations

import json
from typing import Dict, List

from .contracts import QuantumJob, QuantumResult

try:
    import cirq
except Exception:  # pragma: no cover - optional dependency
    cirq = None  # type: ignore


class QuantumAdapterError(RuntimeError):
    """Raised when the TFQ adapter cannot run a job."""


class TFQSimAdapter:
    """Lightweight Cirq-backed simulator adapter."""

    def __init__(self) -> None:
        self._available = cirq is not None

    def run(self, job: QuantumJob) -> QuantumResult:
        if not self._available or cirq is None:
            raise QuantumAdapterError("Cirq is not available in this environment")

        circuit = cirq.read_json(json_text=job.circuit_json)
        repetitions = max(1, int(job.params.get("_bytes", 32)) * 8)

        simulator = cirq.Simulator()
        result = simulator.run(circuit, repetitions=repetitions)

        bitstrings: Dict[str, List[int]] = {}
        for key in job.readouts or ["r"]:
            measurements = result.measurements.get(key, [])
            flattened = measurements.flatten().tolist() if len(measurements) else []
            bitstrings[key] = [int(bit) for bit in flattened]

        # For a simple Hadamard circuit, fidelity approaches 1.0 on simulator.
        fidelity = 0.999
        stats = {"repetitions": float(repetitions)}

        return QuantumResult(
            job_id=job.id,
            bitstrings=bitstrings,
            expectations={},
            fidelity_est=fidelity,
            stats=stats,
        )


__all__ = ["TFQSimAdapter", "QuantumAdapterError"]
