"""Quantum entropy source wiring for Slot 01."""

from __future__ import annotations

import hashlib
import logging
import os
import secrets
from dataclasses import dataclass
from typing import Any, Dict, List, Optional
from uuid import uuid4

from nova.metrics.quantum import record_entropy_job
from nova.quantum import QuantumJob
from nova.quantum.adapter_tfq import TFQSimAdapter, QuantumAdapterError
from nova.quantum.utils import circuit_to_json, make_hadamard_measure_circuit
from nova.slots.config import get_config
from .fidelity import fidelity_from_bits

logger = logging.getLogger(__name__)

DEFAULT_BYTES = 32


@dataclass
class EntropySample:
    """Container for entropy material plus provenance data."""

    data: bytes
    source: str
    backend: str
    fidelity: Optional[float] = None
    fidelity_ci: Optional[tuple[float, float]] = None
    abs_bias: Optional[float] = None
    error: Optional[str] = None

    def digest(self) -> str:
        return hashlib.sha3_256(self.data).hexdigest()


class QuantumEntropySource:
    """Interface to the Quantum Adapter Layer."""

    def __init__(self, backend: str = "simulator", adapter: Optional[TFQSimAdapter] = None) -> None:
        self.backend = backend
        self.adapter = adapter or TFQSimAdapter()

    def sample(self, n_bytes: int = DEFAULT_BYTES) -> EntropySample:
        """Return an entropy sample sourced from the quantum backend."""
        circuit = make_hadamard_measure_circuit(1, key="r")
        circuit_json = circuit_to_json(circuit)
        job = QuantumJob(
            id=str(uuid4()),
            backend=self.backend,  # type: ignore[arg-type]
            circuit_json=circuit_json,
            readouts=["r"],
            params={"_bytes": float(n_bytes)},
        )

        result = self.adapter.run(job)
        bits = _collect_bits(result.bitstrings or {}, "r", n_bytes * 8)
        entropy = _bits_to_bytes(bits, n_bytes)

        # Compute fidelity metrics
        F, (ci_lo, ci_hi), abs_bias = fidelity_from_bits(entropy)
        record_entropy_job(self.backend, True, bytes_out=len(entropy), fidelity=F, fidelity_ci=(ci_lo, ci_hi), abs_bias=abs_bias)

        return EntropySample(
            data=entropy,
            source="quantum",
            backend=self.backend,
            fidelity=F,
            fidelity_ci=(ci_lo, ci_hi),
            abs_bias=abs_bias,
        )


def get_entropy_bytes(n_bytes: Optional[int] = None) -> bytes:
    """Convenience helper that returns only the entropy bytes."""
    return get_entropy_sample(n_bytes).data


def get_entropy_sample(n_bytes: Optional[int] = None) -> EntropySample:
    """Return entropy along with provenance and fidelity when available."""
    settings = _load_slot_settings()
    env_override = os.getenv("NOVA_SLOT01_QUANTUM_ENTROPY_ENABLED")
    quantum_enabled = (
        (env_override.lower() in {"1", "true", "yes", "on"}) if env_override else settings.get("enabled", True)
    )
    backend = os.getenv("NOVA_SLOT01_QUANTUM_BACKEND", settings.get("backend", "simulator"))
    bytes_per_seed = int(settings.get("bytes_per_seed", DEFAULT_BYTES))
    requested_bytes = max(1, n_bytes or bytes_per_seed)
    last_error: Optional[str] = None

    if quantum_enabled:
        try:
            source = QuantumEntropySource(backend=backend)
            return source.sample(requested_bytes)
        except (QuantumAdapterError, RuntimeError) as exc:
            last_error = str(exc)
            logger.warning("Quantum entropy fallback activated: %s", exc)
            record_entropy_job(str(backend), False, bytes_out=0, fidelity=None)

    env_seed = os.getenv("NOVA_ENTROPY_SEED")
    if env_seed:
        digest = hashlib.sha3_256(env_seed.encode("utf-8")).digest()
        entropy = _resize_bytes(digest, requested_bytes)
        # Compute fidelity even for deterministic seed
        F, (ci_lo, ci_hi), abs_bias = fidelity_from_bits(entropy)
        return EntropySample(
            data=entropy,
            source="env_seed",
            backend="seed",
            fidelity=F,
            fidelity_ci=(ci_lo, ci_hi),
            abs_bias=abs_bias,
            error=last_error,
        )

    entropy = secrets.token_bytes(requested_bytes)
    # Compute fidelity for fallback entropy too
    F, (ci_lo, ci_hi), abs_bias = fidelity_from_bits(entropy)
    return EntropySample(
        data=entropy,
        source="fallback",
        backend="os.urandom",
        fidelity=F,
        fidelity_ci=(ci_lo, ci_hi),
        abs_bias=abs_bias,
        error=last_error,
    )


def _load_slot_settings() -> Dict[str, Any]:
    try:
        cfg = get_config() or {}
    except Exception:
        return {}

    slot_cfg = cfg.get("slot01") or cfg.get("slot01_truth_anchor") or {}
    return slot_cfg.get("quantum_entropy", {})


def _collect_bits(store: Dict[str, List[int]], key: str, required_bits: int) -> str:
    values = store.get(key, [])
    bits = "".join(str(bit) for bit in values)
    if len(bits) < required_bits:
        bits = bits.ljust(required_bits, "0")
    return bits[:required_bits]


def _bits_to_bytes(bits: str, n_bytes: int) -> bytes:
    if not bits:
        return bytes(n_bytes)
    value = int(bits, 2)
    return value.to_bytes(n_bytes, "big", signed=False)


def _resize_bytes(data: bytes, n_bytes: int) -> bytes:
    if len(data) == n_bytes:
        return data
    if len(data) > n_bytes:
        return data[:n_bytes]
    repeats = (n_bytes // len(data)) + 1
    expanded = (data * repeats)[:n_bytes]
    return expanded


__all__ = ["QuantumEntropySource", "EntropySample", "get_entropy_sample", "get_entropy_bytes"]
