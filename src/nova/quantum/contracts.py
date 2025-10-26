"""Contracts for Nova's Quantum Adapter Layer."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Literal, Optional

BackendT = Literal["simulator", "google_qcs"]


@dataclass(slots=True)
class QuantumJob:
    """Description of a quantum execution request."""

    id: str
    backend: BackendT
    circuit_json: str
    readouts: List[str] = field(default_factory=lambda: ["r"])
    params: Dict[str, float] = field(default_factory=dict)


@dataclass(slots=True)
class QuantumResult:
    """Minimal execution result payload."""

    job_id: str
    bitstrings: Optional[Dict[str, List[int]]]
    expectations: Dict[str, float] = field(default_factory=dict)
    fidelity_est: Optional[float] = None
    stats: Dict[str, float] = field(default_factory=dict)


__all__ = ["QuantumJob", "QuantumResult", "BackendT"]
