"""Adaptive wisdom core: Jacobian provider for bifurcation-aware control.

Implements reduced 3×3 dynamics:
  dγ/dt = η(Q - γ)     # Wisdom learning
  dS/dt = a₁(S_ref - S) - a₂η  # Stability tracking
  dη/dt = k_p(S - S_ref) - k_d η  # PD controller

Jacobian at equilibrium (γ*, S*, η*) = (Q, S_ref, η₀):
  J = [[-η*,  0,   0  ],
       [ 0,  -a₁, -a₂ ],
       [ 0,   k_p, -k_d]]
"""

from __future__ import annotations

import os
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Dict

import numpy as np

__all__ = ["JacobianProvider", "ThreeDProvider", "State3D", "Params3D"]


@dataclass(frozen=True)
class State3D:
    """State vector for 3D reduced system."""

    gamma: float  # Wisdom level
    S: float  # Stability margin
    eta: float  # Learning rate


@dataclass(frozen=True)
class Params3D:
    """Parameters for 3D reduced dynamics."""

    Q: float  # Quality target for wisdom
    S_ref: float  # Reference stability margin
    a1: float  # Stability restoration rate
    a2: float  # Stability cost of learning
    k_p: float  # Proportional gain
    k_d: float  # Derivative gain

    @classmethod
    def from_env(cls) -> "Params3D":
        """Load parameters from environment with defaults."""
        return cls(
            Q=float(os.getenv("NOVA_WISDOM_Q", "0.7")),
            S_ref=float(os.getenv("NOVA_WISDOM_S_REF", "0.05")),
            a1=float(os.getenv("NOVA_WISDOM_A1", "0.2")),
            a2=float(os.getenv("NOVA_WISDOM_A2", "0.1")),
            k_p=float(os.getenv("NOVA_WISDOM_KP", "0.3")),
            k_d=float(os.getenv("NOVA_WISDOM_KD", "0.15")),
        )


class JacobianProvider(ABC):
    """Interface for pluggable Jacobian computation."""

    @abstractmethod
    def params(self) -> Dict[str, float]:
        """Return current parameter dictionary."""

    @abstractmethod
    def jacobian(self, state: State3D) -> np.ndarray:
        """Compute Jacobian at given state."""


class ThreeDProvider(JacobianProvider):
    """3×3 reduced system Jacobian provider."""

    def __init__(self, params: Params3D | None = None):
        self._params = params or Params3D.from_env()

    def params(self) -> Dict[str, float]:
        return {
            "Q": self._params.Q,
            "S_ref": self._params.S_ref,
            "a1": self._params.a1,
            "a2": self._params.a2,
            "k_p": self._params.k_p,
            "k_d": self._params.k_d,
        }

    def jacobian(self, state: State3D) -> np.ndarray:
        """Compute 3×3 Jacobian at equilibrium-linearized point.

        J = [[-η*,  0,   0  ],
             [ 0,  -a₁, -a₂ ],
             [ 0,   k_p, -k_d]]

        Note: First eigenvalue is -η* (always stable if η > 0).
        Second/third from 2×2 block can form complex conjugate pair → Hopf.
        """
        p = self._params
        eta = state.eta

        return np.array(
            [
                [-eta, 0.0, 0.0],
                [0.0, -p.a1, -p.a2],
                [0.0, p.k_p, -p.k_d],
            ]
        )


if __name__ == "__main__":
    # Quick verification
    provider = ThreeDProvider()
    state = State3D(gamma=0.7, S=0.05, eta=0.10)
    J = provider.jacobian(state)
    eigs = np.linalg.eigvals(J)

    print(f"Parameters: {provider.params()}")
    print(f"State: γ={state.gamma}, S={state.S}, η={state.eta}")
    print(f"Jacobian:\n{J}")
    print(f"Eigenvalues: {eigs}")
    print(f"Spectral radius: {np.max(np.abs(eigs)):.4f}")
    print(f"Stability margin: {-np.max(np.real(eigs)):.4f}")
