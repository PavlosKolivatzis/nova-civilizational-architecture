#!/usr/bin/env python3
"""
Nova ORP Convergence Matrix Generation
Phase 11 - Stability Loop Convergence Analysis
"""

from enum import Enum
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import numpy as np
import json

from regime_state_machine import Regime

@dataclass
class ConvergenceMetrics:
    kappa_state: float  # State contraction rate λ_min(H)
    kappa_energy: float  # Energy contraction rate 2λ_min(H)
    stability_margin: float  # Distance to Hopf bifurcation
    convergence_time: float  # Expected time to converge (seconds)
    oscillation_risk: float  # Probability of oscillation [0,1]
    recovery_rate: float  # Rate of return to equilibrium

class ConvergenceMatrix:
    def __init__(self):
        self.regimes = [r for r in Regime if r != Regime.UNKNOWN]
        self.matrix: Dict[Tuple[Regime, Regime], ConvergenceMetrics] = {}

        # Initialize convergence matrix with regime-specific properties
        self._build_convergence_matrix()

    def _build_convergence_matrix(self):
        """Build the convergence matrix based on regime characteristics"""

        # Base convergence properties per regime
        regime_properties = {
            Regime.NORMAL: {
                "kappa_state": 0.95,  # Fast convergence
                "stability_margin": 0.8,
                "convergence_time": 30.0,
                "oscillation_risk": 0.05,
                "recovery_rate": 0.9
            },
            Regime.HEIGHTENED: {
                "kappa_state": 0.85,
                "stability_margin": 0.6,
                "convergence_time": 120.0,
                "oscillation_risk": 0.15,
                "recovery_rate": 0.7
            },
            Regime.CONTROLLED_DEGRADATION: {
                "kappa_state": 0.70,
                "stability_margin": 0.4,
                "convergence_time": 300.0,
                "oscillation_risk": 0.30,
                "recovery_rate": 0.5
            },
            Regime.EMERGENCY_STABILIZATION: {
                "kappa_state": 0.50,
                "stability_margin": 0.2,
                "convergence_time": 600.0,
                "oscillation_risk": 0.50,
                "recovery_rate": 0.3
            },
            Regime.RECOVERY: {
                "kappa_state": 0.75,
                "stability_margin": 0.5,
                "convergence_time": 900.0,
                "oscillation_risk": 0.25,
                "recovery_rate": 0.6
            }
        }

        # Build transition matrix
        for from_regime in self.regimes:
            for to_regime in self.regimes:
                from_props = regime_properties[from_regime]
                to_props = regime_properties[to_regime]

                # Calculate transition convergence metrics
                # Same regime: maintain stability
                if from_regime == to_regime:
                    kappa_state = from_props["kappa_state"]
                    stability_margin = from_props["stability_margin"]
                    convergence_time = from_props["convergence_time"]
                    oscillation_risk = from_props["oscillation_risk"]
                    recovery_rate = from_props["recovery_rate"]

                # Transition to more stable regime: faster convergence
                elif list(Regime).index(from_regime) > list(Regime).index(to_regime):
                    kappa_state = min(from_props["kappa_state"] * 1.2, to_props["kappa_state"] * 1.1)
                    stability_margin = (from_props["stability_margin"] + to_props["stability_margin"]) / 2
                    convergence_time = from_props["convergence_time"] * 0.7
                    oscillation_risk = from_props["oscillation_risk"] * 0.8
                    recovery_rate = (from_props["recovery_rate"] + to_props["recovery_rate"]) / 2

                # Transition to less stable regime: slower convergence
                else:
                    kappa_state = max(from_props["kappa_state"] * 0.8, to_props["kappa_state"] * 0.9)
                    stability_margin = min(from_props["stability_margin"], to_props["stability_margin"])
                    convergence_time = from_props["convergence_time"] * 1.5
                    oscillation_risk = from_props["oscillation_risk"] * 1.2
                    recovery_rate = min(from_props["recovery_rate"], to_props["recovery_rate"])

                # Hysteresis effect: transitions take longer due to minimum durations
                if from_regime != to_regime:
                    convergence_time *= 1.3  # Account for hysteresis delay

                kappa_energy = 2 * kappa_state  # Standard relationship

                metrics = ConvergenceMetrics(
                    kappa_state=kappa_state,
                    kappa_energy=kappa_energy,
                    stability_margin=stability_margin,
                    convergence_time=convergence_time,
                    oscillation_risk=min(oscillation_risk, 1.0),
                    recovery_rate=recovery_rate
                )

                self.matrix[(from_regime, to_regime)] = metrics

    def get_convergence_metrics(self, from_regime: Regime, to_regime: Regime) -> ConvergenceMetrics:
        """Get convergence metrics for a specific transition"""
        return self.matrix.get((from_regime, to_regime), self._default_metrics())

    def _default_metrics(self) -> ConvergenceMetrics:
        """Default convergence metrics"""
        return ConvergenceMetrics(
            kappa_state=0.8,
            kappa_energy=1.6,
            stability_margin=0.5,
            convergence_time=180.0,
            oscillation_risk=0.2,
            recovery_rate=0.6
        )

    def generate_stability_loop_matrix(self) -> np.ndarray:
        """Generate the stability loop convergence matrix"""
        n = len(self.regimes)
        matrix = np.zeros((n, n))

        for i, from_regime in enumerate(self.regimes):
            for j, to_regime in enumerate(self.regimes):
                metrics = self.get_convergence_metrics(from_regime, to_regime)
                # Use kappa_state as the convergence measure
                matrix[i, j] = metrics.kappa_state

        return matrix

    def analyze_system_stability(self) -> Dict[str, float]:
        """Analyze overall system stability properties"""
        matrix = self.generate_stability_loop_matrix()

        return {
            "spectral_radius": float(np.max(np.abs(np.linalg.eigvals(matrix)))),
            "condition_number": float(np.linalg.cond(matrix)),
            "determinant": float(np.linalg.det(matrix)),
            "trace": float(np.trace(matrix)),
            "average_convergence_rate": float(np.mean(matrix)),
            "min_convergence_rate": float(np.min(matrix)),
            "max_convergence_rate": float(np.max(matrix))
        }

    def print_convergence_matrix(self):
        """Print the convergence matrix in human-readable format"""
        print("Nova ORP Convergence Matrix")
        print("=" * 50)
        print("Regime Transition Convergence Rates (kappa_state)")
        print("-" * 50)

        # Header
        print("From \\ To".ljust(25), end="")
        for regime in self.regimes:
            print(f"{regime.value[:8]:>8}", end="")
        print()

        # Matrix rows
        for from_regime in self.regimes:
            print(f"{from_regime.value:<25}", end="")
            for to_regime in self.regimes:
                metrics = self.get_convergence_metrics(from_regime, to_regime)
                print(f"{metrics.kappa_state:>8.3f}", end="")
            print()

        print("\nStability Loop Analysis:")
        stability = self.analyze_system_stability()
        for key, value in stability.items():
            print(f"  {key}: {value:.4f}")

    def export_to_json(self, filename: str = "convergence_matrix.json"):
        """Export convergence matrix to JSON"""
        data = {
            "regimes": [r.value for r in self.regimes],
            "matrix": {},
            "stability_analysis": self.analyze_system_stability()
        }

        for (from_regime, to_regime), metrics in self.matrix.items():
            key = f"{from_regime.value}_to_{to_regime.value}"
            data["matrix"][key] = {
                "kappa_state": metrics.kappa_state,
                "kappa_energy": metrics.kappa_energy,
                "stability_margin": metrics.stability_margin,
                "convergence_time": metrics.convergence_time,
                "oscillation_risk": metrics.oscillation_risk,
                "recovery_rate": metrics.recovery_rate
            }

        with open(filename, 'w') as f:
            json.dump(data, f, indent=2)

def main():
    matrix = ConvergenceMatrix()
    matrix.print_convergence_matrix()

    print("\nDetailed Transition Analysis:")
    print("-" * 40)

    # Analyze some key transitions
    transitions = [
        (Regime.NORMAL, Regime.HEIGHTENED),
        (Regime.HEIGHTENED, Regime.NORMAL),
        (Regime.EMERGENCY_STABILIZATION, Regime.RECOVERY),
        (Regime.RECOVERY, Regime.NORMAL),
        (Regime.CONTROLLED_DEGRADATION, Regime.CONTROLLED_DEGRADATION)  # Same regime
    ]

    for from_regime, to_regime in transitions:
        metrics = matrix.get_convergence_metrics(from_regime, to_regime)
        transition_type = "Same Regime" if from_regime == to_regime else "Transition"

        print(f"\n{transition_type}: {from_regime.value} -> {to_regime.value}")
        print(f"  State Convergence Rate (kappa_state): {metrics.kappa_state:.3f}")
        print(f"  Energy Convergence Rate (kappa_energy): {metrics.kappa_energy:.3f}")
        print(f"  Stability Margin: {metrics.stability_margin:.3f}")
        print(f"  Expected Convergence Time: {metrics.convergence_time:.1f}s")
        print(f"  Oscillation Risk: {metrics.oscillation_risk:.3f}")
        print(f"  Recovery Rate: {metrics.recovery_rate:.3f}")

    # Export to JSON
    matrix.export_to_json()
    print(f"\nConvergence matrix exported to convergence_matrix.json")

if __name__ == "__main__":
    main()