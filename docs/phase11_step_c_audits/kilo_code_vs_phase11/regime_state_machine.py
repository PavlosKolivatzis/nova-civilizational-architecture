#!/usr/bin/env python3
"""
Nova Operational Regime Policy (ORP) State Machine Reconstruction
Phase 11 - System Invariants Implementation
"""

from enum import Enum
from typing import Dict, List, Set, Tuple, Optional
import json

class Regime(Enum):
    NORMAL = "normal"
    HEIGHTENED = "heightened"
    CONTROLLED_DEGRADATION = "controlled_degradation"
    EMERGENCY_STABILIZATION = "emergency_stabilization"
    RECOVERY = "recovery"
    UNKNOWN = "unknown"

class RegimeStateMachine:
    def __init__(self):
        self.regimes = list(Regime)
        self.allowed_transitions: Dict[Regime, Set[Regime]] = {
            Regime.NORMAL: {Regime.HEIGHTENED},
            Regime.HEIGHTENED: {Regime.NORMAL, Regime.CONTROLLED_DEGRADATION},
            Regime.CONTROLLED_DEGRADATION: {Regime.HEIGHTENED, Regime.EMERGENCY_STABILIZATION},
            Regime.EMERGENCY_STABILIZATION: {Regime.RECOVERY},
            Regime.RECOVERY: {Regime.HEIGHTENED}
        }

        self.forbidden_direct: Set[Tuple[Regime, Regime]] = {
            (Regime.NORMAL, Regime.EMERGENCY_STABILIZATION),
            (Regime.NORMAL, Regime.RECOVERY),
            (Regime.HEIGHTENED, Regime.EMERGENCY_STABILIZATION)
        }

        self.min_durations: Dict[Regime, int] = {
            Regime.NORMAL: 60,
            Regime.HEIGHTENED: 300,
            Regime.CONTROLLED_DEGRADATION: 600,
            Regime.EMERGENCY_STABILIZATION: 900,
            Regime.RECOVERY: 1800
        }

    def is_transition_allowed(self, from_regime: Regime, to_regime: Regime) -> bool:
        """Check if direct transition is allowed (ignoring hysteresis)"""
        return to_regime in self.allowed_transitions.get(from_regime, set())

    def get_allowed_transitions(self, from_regime: Regime) -> Set[Regime]:
        """Get all allowed transitions from a regime"""
        return self.allowed_transitions.get(from_regime, set())

    def get_forbidden_transitions(self) -> Set[Tuple[Regime, Regime]]:
        """Get all explicitly forbidden direct transitions"""
        return self.forbidden_direct

    def get_min_duration(self, regime: Regime) -> int:
        """Get minimum duration for a regime in seconds"""
        return self.min_durations[regime]

    def to_graphviz(self) -> str:
        """Generate GraphViz DOT representation of the state machine"""
        lines = ["digraph RegimeStateMachine {", "    rankdir=LR;", "    node [shape=circle];"]

        # Add nodes
        for regime in self.regimes:
            lines.append(f'    {regime.value} [label="{regime.value}\\n{min(self.min_durations[regime]//60, 30)}min"];')

        # Add edges
        for from_regime, to_regimes in self.allowed_transitions.items():
            for to_regime in to_regimes:
                lines.append(f'    {from_regime.value} -> {to_regime.value};')

        lines.append("}")
        return "\n".join(lines)

    def __str__(self) -> str:
        return f"RegimeStateMachine with {len(self.regimes)} regimes and {sum(len(t) for t in self.allowed_transitions.values())} allowed transitions"

if __name__ == "__main__":
    sm = RegimeStateMachine()
    print("Regime State Machine Reconstruction")
    print("=" * 40)
    print(sm)
    print("\nAllowed Transitions:")
    for from_regime in sm.regimes:
        allowed = sm.get_allowed_transitions(from_regime)
        print(f"  {from_regime.value} -> {', '.join(r.value for r in allowed)}")

    print("\nForbidden Direct Transitions:")
    for from_r, to_r in sm.get_forbidden_transitions():
        print(f"  {from_r.value} -> {to_r.value}")

    print("\nMinimum Durations:")
    for regime, duration in sm.min_durations.items():
        print(f"  {regime.value}: {duration}s ({duration//60}min)")

    print("\nGraphViz DOT:")
    print(sm.to_graphviz())