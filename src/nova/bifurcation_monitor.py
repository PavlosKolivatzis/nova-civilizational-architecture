"""Bifurcation detection and stability analysis via eigenvalue decomposition.

Computes from Jacobian eigenvalues:
  ρ (rho) = max |λᵢ|        Spectral radius (overall gain)
  S       = -max Re(λᵢ)     Stability margin (distance from instability)
  H       = min |Re(λ)| for oscillatory modes  (Hopf distance)

Alerts:
  - S ≤ 0: Instability detected
  - H < H_min: Near Hopf bifurcation (oscillations imminent)
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List

import numpy as np

__all__ = ["BifurcationMonitor", "StabilityAnalysis"]


@dataclass(frozen=True)
class StabilityAnalysis:
    """Results of eigenvalue-based stability analysis."""

    rho: float  # Spectral radius max|λ|
    S: float  # Stability margin -max(Re(λ))
    H: float  # Hopf distance min|Re(λ)| for oscillatory modes
    stable: bool  # S > 0
    hopf_risk: bool  # H < threshold
    eigenvalues: List[complex]  # All eigenvalues
    oscillatory_freqs: List[float]  # |Im(λ)| for complex pairs


class BifurcationMonitor:
    """Real-time bifurcation detection from Jacobian eigenvalues."""

    def __init__(
        self,
        hopf_threshold: float = 0.02,
        osc_imaginary_min: float = 1e-3,
    ):
        """Initialize monitor.

        Args:
            hopf_threshold: H threshold for Hopf risk alert
            osc_imaginary_min: Min |Im(λ)| to classify as oscillatory
        """
        self.hopf_threshold = hopf_threshold
        self.osc_imaginary_min = osc_imaginary_min

    def analyze(self, jacobian: np.ndarray) -> StabilityAnalysis:
        """Analyze stability from Jacobian eigenvalues.

        Args:
            jacobian: N×N Jacobian matrix at current state

        Returns:
            StabilityAnalysis with ρ, S, H and flags
        """
        eigenvalues = np.linalg.eigvals(jacobian)
        eig_list = [complex(lam) for lam in eigenvalues]

        # Spectral radius: max |λ|
        rho = float(np.max(np.abs(eigenvalues)))

        # Stability margin: -max Re(λ)
        # Stable if all Re(λ) < 0, so S > 0
        max_real = float(np.max(np.real(eigenvalues)))
        S = -max_real
        stable = S > 0

        # Hopf distance: min |Re(λ)| for oscillatory modes
        # Oscillatory: |Im(λ)| > threshold
        oscillatory_modes = [
            lam for lam in eigenvalues if np.abs(np.imag(lam)) > self.osc_imaginary_min
        ]

        if oscillatory_modes:
            H = float(np.min(np.abs(np.real(oscillatory_modes))))
            oscillatory_freqs = [float(np.abs(np.imag(lam))) for lam in oscillatory_modes]
        else:
            H = float("inf")  # No oscillatory modes
            oscillatory_freqs = []

        hopf_risk = H < self.hopf_threshold

        return StabilityAnalysis(
            rho=rho,
            S=S,
            H=H,
            stable=stable,
            hopf_risk=hopf_risk,
            eigenvalues=eig_list,
            oscillatory_freqs=oscillatory_freqs,
        )


if __name__ == "__main__":
    # Test with known Jacobian
    monitor = BifurcationMonitor(hopf_threshold=0.02)

    # Stable case
    J_stable = np.array([[-0.10, 0.0, 0.0], [0.0, -0.20, -0.10], [0.0, 0.30, -0.15]])

    analysis = monitor.analyze(J_stable)
    print("=== Stable Case ===")
    print(f"ρ (spectral radius): {analysis.rho:.4f}")
    print(f"S (stability margin): {analysis.S:.4f}")
    print(f"H (Hopf distance): {analysis.H:.4f}")
    print(f"Stable: {analysis.stable}")
    print(f"Hopf risk: {analysis.hopf_risk}")
    print(f"Eigenvalues: {[f'{lam:.4f}' for lam in analysis.eigenvalues]}")
    print(f"Oscillatory frequencies: {analysis.oscillatory_freqs}\n")

    # Near-Hopf case (smaller k_d → oscillations)
    J_hopf = np.array([[-0.10, 0.0, 0.0], [0.0, -0.20, -0.10], [0.0, 0.50, -0.05]])

    analysis_hopf = monitor.analyze(J_hopf)
    print("=== Near-Hopf Case ===")
    print(f"ρ (spectral radius): {analysis_hopf.rho:.4f}")
    print(f"S (stability margin): {analysis_hopf.S:.4f}")
    print(f"H (Hopf distance): {analysis_hopf.H:.4f}")
    print(f"Stable: {analysis_hopf.stable}")
    print(f"Hopf risk: {analysis_hopf.hopf_risk}")
    print(f"Eigenvalues: {[f'{lam:.4f}' for lam in analysis_hopf.eigenvalues]}")
    print(f"Oscillatory frequencies: {[f'{freq:.4f}' for freq in analysis_hopf.oscillatory_freqs]}")
