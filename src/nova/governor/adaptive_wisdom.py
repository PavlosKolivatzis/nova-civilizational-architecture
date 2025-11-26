# Nominal Sufficiency Rule:
# Do not add config keys, files, or telemetry unless they reduce false alerts
# or improve (C, rho, S, H, gamma, eta) stability. PRs violating this are rejected.

from __future__ import annotations

import os as _os
from dataclasses import dataclass as _dataclass
from typing import Literal as _Literal

from nova.config.thresholds import WisdomThresholds as _WisdomThresholds
from nova.config.thresholds import load_wisdom_thresholds as _load_wisdom_thresholds

# Phase 11.3 Step 2: ORP η scaling integration (optional, flag-gated)
try:
    from src.nova.continuity.eta_scaling import apply_eta_scaling as _apply_eta_scaling
    from src.nova.continuity.regime_transition_ledger import get_current_regime_duration as _get_regime_duration
except Exception:  # pragma: no cover
    def _apply_eta_scaling(eta_base, regime, duration_s, freeze=False):  # type: ignore[misc]
        return eta_base  # No scaling if imports fail
    def _get_regime_duration():  # type: ignore[misc]
        return {"regime": "normal", "duration_s": 0.0}

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

    def __init__(
        self,
        eta: float = 0.10,
        eta_min: float = 0.05,
        eta_max: float = 0.15,
        *,
        thresholds: _WisdomThresholds | None = None,
    ) -> None:
        self.eta = float(eta)
        self.eta_min = float(eta_min)
        self.eta_max = float(eta_max)
        if self.eta_min > self.eta_max:
            self.eta_min, self.eta_max = self.eta_max, self.eta_min
        self.eta = max(self.eta_min, min(self.eta, self.eta_max))
        self._thresholds = thresholds or _load_wisdom_thresholds()

    def step(self, margin: float, G: float) -> Telemetry:
        """Update eta based on margin (-Re(lambda_max)) and generativity G.

        Phase 11.3: Applies ORP regime scaling if NOVA_ENABLE_ETA_SCALING=1.
        """

        config = self._thresholds

        # Compute base eta from margin/generativity
        if margin < config.critical_margin:
            eta_base = self.eta_min
            mode = "CRITICAL"
        elif margin < config.stabilizing_margin:
            eta_base = max(self.eta_min, 0.08)
            mode = "STABILIZING"
        elif margin > config.exploring_margin and G < config.exploring_g:
            eta_base = min(self.eta_max, self.eta * 1.10, 0.18)
            mode = "EXPLORING"
        elif margin > config.optimal_margin and G >= config.optimal_g:
            eta_base = max(self.eta_min, min(self.eta_max, 0.12))
            mode = "OPTIMAL"
        else:
            eta_base = max(self.eta_min, min(self.eta_max, 0.08))
            mode = "SAFE"

        # Phase 11.3: Apply ORP regime scaling if enabled
        if _os.getenv("NOVA_ENABLE_ETA_SCALING", "0") == "1":
            try:
                regime_info = _get_regime_duration()
                eta_scaled = _apply_eta_scaling(
                    eta_base=eta_base,
                    regime=regime_info["regime"],
                    duration_s=regime_info["duration_s"],
                    freeze=False  # Freeze handled elsewhere if needed
                )
                # Clamp to Governor's eta_min/eta_max bounds
                self.eta = max(self.eta_min, min(self.eta_max, eta_scaled))
            except Exception:
                # Fallback to base eta if ORP scaling fails
                self.eta = eta_base
        else:
            self.eta = eta_base

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

    governor = AdaptiveWisdomGovernor(
        eta=eta_default,
        eta_min=eta_min,
        eta_max=eta_max,
        thresholds=_load_wisdom_thresholds(),
    )
    telemetry = governor.step(args.margin, args.g)
    print(f"mode={telemetry.mode} eta={telemetry.eta:.4f} margin={telemetry.margin:.4f} G={telemetry.G:.4f}")
