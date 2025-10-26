"""Quantum entropy Prometheus metrics helpers."""

from __future__ import annotations

from typing import Optional

from prometheus_client import Counter, Gauge

from .registry import REGISTRY

_entropy_jobs = Counter(
    "slot01_entropy_quantum_jobs_total",
    "Total quantum entropy jobs executed",
    ["backend", "status"],
    registry=REGISTRY,
)

_entropy_bytes = Counter(
    "slot01_entropy_bytes_generated_total",
    "Total entropy bytes generated via quantum adapter",
    registry=REGISTRY,
)

_entropy_failures = Counter(
    "slot01_entropy_failures_total",
    "Total quantum entropy job failures",
    registry=REGISTRY,
)

_entropy_fidelity = Gauge(
    "slot01_entropy_fidelity_mean",
    "Last observed quantum fidelity estimate for Slot01 entropy source",
    registry=REGISTRY,
)


def record_entropy_job(
    backend: str,
    success: bool,
    *,
    bytes_out: int = 0,
    fidelity: Optional[float] = None,
) -> None:
    """Record the outcome of a quantum entropy request."""
    status = "ok" if success else "error"
    _entropy_jobs.labels(backend=backend, status=status).inc()

    if success:
        if bytes_out > 0:
            _entropy_bytes.inc(bytes_out)
        if fidelity is not None:
            _entropy_fidelity.set(fidelity)
    else:
        _entropy_failures.inc()


__all__ = ["record_entropy_job"]
