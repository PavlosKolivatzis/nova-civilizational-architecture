# Nominal Sufficiency Rule:
# Do not add config keys, files, or telemetry unless they reduce false alerts
# or improve (C, rho, S, H, gamma, eta) stability. PRs violating this are rejected.

from __future__ import annotations

from dataclasses import dataclass as _dataclass
from typing import Literal as _Literal

__all__ = ["AdaptiveWisdomGovernor", "Telemetry", "State"]


@_dataclass(frozen=True)
class State:
    rho: float
    S: float
    C: float
    H: float
    gamma: float


@_dataclass(frozen=True)
class Telemetry:
    eta: float
    margin: float
    G: float
    mode: _Literal["CRITICAL", "STABILIZING", "EXPLORING", "OPTIMAL", "SAFE"]


class AdaptiveWisdomGovernor:
    """Minimal adaptive controller for gamma-learning rate."""

    def __init__(self, eta: float = 0.10, eta_min: float = 0.05, eta_max: float = 0.15) -> None:
        self.eta = float(eta)
        self.eta_min = float(eta_min)
        self.eta_max = float(eta_max)
        if self.eta_min > self.eta_max:
            self.eta_min, self.eta_max = self.eta_max, self.eta_min
        self.eta = max(self.eta_min, min(self.eta, self.eta_max))

    def step(self, margin: float, G: float) -> Telemetry:
        """Update eta based on margin (-Re(lambda_max)) and generativity G."""

        if margin < 0.01:
            self.eta = self.eta_min
            mode = "CRITICAL"
        elif margin < 0.02:
            self.eta = max(self.eta_min, 0.08)
            mode = "STABILIZING"
        elif margin > 0.10 and G < 0.60:
            self.eta = min(self.eta_max, self.eta * 1.10, 0.18)
            mode = "EXPLORING"
        elif margin > 0.05 and G >= 0.70:
            self.eta = max(self.eta_min, min(self.eta_max, 0.12))
            mode = "OPTIMAL"
        else:
            self.eta = max(self.eta_min, min(self.eta_max, 0.08))
            mode = "SAFE"

        return Telemetry(eta=self.eta, margin=margin, G=G, mode=mode)


if __name__ == "__main__":
    import argparse
    import os

    parser = argparse.ArgumentParser(description="Adaptive Wisdom Governor CLI")
    parser.add_argument("--margin", type=float, required=True, help="-Re(lambda_max)")
    parser.add_argument("--g", type=float, required=True, help="Generativity score")
    args = parser.parse_args()

    eta_min = float(os.getenv("NOVA_GAMMA_ETA_MIN", "0.05"))
    eta_max = float(os.getenv("NOVA_GAMMA_ETA_MAX", "0.15"))
    eta_default = float(os.getenv("NOVA_GAMMA_ETA_DEFAULT", "0.10"))

    governor = AdaptiveWisdomGovernor(eta=eta_default, eta_min=eta_min, eta_max=eta_max)
    telemetry = governor.step(args.margin, args.g)
    print(f"mode={telemetry.mode} eta={telemetry.eta:.4f} margin={telemetry.margin:.4f} G={telemetry.G:.4f}")
