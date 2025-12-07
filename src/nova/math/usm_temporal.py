"""
Temporal USM Stabilization Layer (Phase 14.5)

Pure mathematical kernel for temporal evolution of USM metrics:
    - H_t: spectral entropy (structural complexity)
    - rho_t: equilibrium ratio (protective/extractive balance)
    - C_t: collapse score (factory-mode risk)

This module is intentionally:
    - Pure (no side effects, no IO)
    - Slot-agnostic (owned by Slot02 but usable by tests)
    - Flag-agnostic (integration decides when/how to call it)

See: docs/specs/phase14_5_temporal_usm_spec.md
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass
class TemporalUsmState:
    """
    Temporal USM state for a single processing stream.

    Attributes:
        H: Temporal spectral entropy H_t
        rho: Temporal equilibrium ratio rho_t
        C: Temporal collapse score C_t
    """

    H: float
    rho: float
    C: float


def _validate_lambda(lambda_: float) -> None:
    """Validate decay/smoothing constant."""
    if not (0.0 < lambda_ < 1.0):
        raise ValueError(f"lambda must be in (0, 1), got {lambda_!r}")


def step_non_void(
    prev: Optional[TemporalUsmState],
    H_inst: float,
    rho_inst: float,
    C_inst: float,
    lambda_: float,
) -> TemporalUsmState:
    """
    Update temporal USM state for a non-VOID input (structure present).

    Implements exponential smoothing:
        H_t   = (1 - λ) * H_{t-1} + λ * H_inst
        rho_t = (1 - λ) * rho_{t-1} + λ * rho_inst
        C_t   = (1 - λ) * C_{t-1} + λ * C_inst

    If prev is None, initialize directly from instantaneous values.
    """
    _validate_lambda(lambda_)

    if prev is None:
        return TemporalUsmState(H=H_inst, rho=rho_inst, C=C_inst)

    H_t = (1.0 - lambda_) * prev.H + lambda_ * H_inst
    rho_t = (1.0 - lambda_) * prev.rho + lambda_ * rho_inst
    C_t = (1.0 - lambda_) * prev.C + lambda_ * C_inst

    return TemporalUsmState(H=H_t, rho=rho_t, C=C_t)


def step_void(
    prev: Optional[TemporalUsmState],
    lambda_: float,
    rho_eq: float = 1.0,
) -> TemporalUsmState:
    """
    Update temporal USM state for a VOID input (no reliable structure).

    Implements soft-reset decay toward equilibrium:
        H_t   = H_{t-1} * λ
        rho_t = rho_{t-1} * λ + (1 - λ) * rho_eq
        C_t   = C_{t-1} * λ

    If prev is None, treat as already at equilibrium:
        H_0 = 0.0, rho_0 = rho_eq, C_0 = 0.0
    """
    _validate_lambda(lambda_)

    if prev is None:
        return TemporalUsmState(H=0.0, rho=rho_eq, C=0.0)

    H_t = prev.H * lambda_
    rho_t = prev.rho * lambda_ + (1.0 - lambda_) * rho_eq
    C_t = prev.C * lambda_

    return TemporalUsmState(H=H_t, rho=rho_t, C=C_t)


__all__ = ["TemporalUsmState", "step_non_void", "step_void"]

