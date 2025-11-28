#!/usr/bin/env python3
"""
Nova ORP Transition Simulation: Legal vs Illegal Transitions
Phase 11 - Testing regime transitions with hysteresis enforcement
"""

from enum import Enum
from typing import List, Dict, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
import time
import json

# Import our modules
from regime_state_machine import RegimeStateMachine, Regime
from hysteresis_rules import HysteresisEngine, HysteresisDecision

class TransitionResult(Enum):
    LEGAL_ALLOWED = "legal_allowed"
    LEGAL_BLOCKED = "legal_blocked"  # Allowed by state machine but blocked by hysteresis
    ILLEGAL_FORBIDDEN = "illegal_forbidden"  # Forbidden by state machine
    ILLEGAL_INVALID = "illegal_invalid"  # Invalid regime

@dataclass
class SimulationStep:
    timestamp: datetime
    current_regime: Regime
    proposed_regime: Regime
    duration_in_current: float
    continuity_score: float
    decision: HysteresisDecision
    result: TransitionResult
    notes: str

class TransitionSimulator:
    def __init__(self):
        self.state_machine = RegimeStateMachine()
        self.hysteresis_engine = HysteresisEngine()
        self.current_regime = Regime.NORMAL
        self.current_duration = 0.0
        self.simulation_steps: List[SimulationStep] = []
        self.start_time = datetime.now()

    def simulate_transition(self,
                          proposed_regime: Regime,
                          duration_override: float = None,
                          continuity_score: float = 1.0,
                          notes: str = "") -> SimulationStep:
        """Simulate a single transition attempt"""

        # Use override duration if provided, otherwise current
        duration = duration_override if duration_override is not None else self.current_duration

        # Check if transition is allowed by state machine
        state_machine_allowed = self.state_machine.is_transition_allowed(self.current_regime, proposed_regime)

        # Check hysteresis
        hysteresis_decision = self.hysteresis_engine.check_regime_hysteresis(
            proposed_regime=proposed_regime,
            current_regime=self.current_regime,
            current_duration_s=duration,
            continuity_score=continuity_score
        )

        # Determine result type
        if proposed_regime not in [r for r in Regime]:
            result = TransitionResult.ILLEGAL_INVALID
        elif not state_machine_allowed:
            result = TransitionResult.ILLEGAL_FORBIDDEN
        elif hysteresis_decision.allowed:
            result = TransitionResult.LEGAL_ALLOWED
        else:
            result = TransitionResult.LEGAL_BLOCKED

        step = SimulationStep(
            timestamp=datetime.now(),
            current_regime=self.current_regime,
            proposed_regime=proposed_regime,
            duration_in_current=duration,
            continuity_score=continuity_score,
            decision=hysteresis_decision,
            result=result,
            notes=notes
        )

        self.simulation_steps.append(step)

        # If transition is actually allowed, update state
        if result == TransitionResult.LEGAL_ALLOWED:
            # Record transition in hysteresis engine
            self.hysteresis_engine.record_transition(
                from_regime=self.current_regime,
                to_regime=proposed_regime,
                duration_s=duration
            )

            # Update current state
            self.current_regime = proposed_regime
            self.current_duration = 0.0
        elif result == TransitionResult.LEGAL_BLOCKED:
            # Stay in current regime, increment duration
            self.current_duration += 10.0  # Simulate 10s passing

        return step

    def run_simulation_scenarios(self) -> List[SimulationStep]:
        """Run predefined simulation scenarios"""

        scenarios = [
            # Scenario 1: Normal operation
            (Regime.NORMAL, 120.0, 1.0, "Normal operation - same regime"),
            (Regime.HEIGHTENED, 120.0, 1.0, "Normal to heightened - allowed"),

            # Scenario 2: Hysteresis blocking
            (Regime.NORMAL, 50.0, 1.0, "Heightened to normal - too early (blocked)"),
            (Regime.NORMAL, 350.0, 1.0, "Heightened to normal - after min duration (allowed)"),

            # Scenario 3: Forbidden transitions
            (Regime.NORMAL, 120.0, 1.0, "Normal to emergency - forbidden"),
            (Regime.HEIGHTENED, 350.0, 1.0, "Heightened to emergency - forbidden"),

            # Scenario 4: Recovery stabilization
            (Regime.EMERGENCY_STABILIZATION, 950.0, 1.0, "Emergency to recovery - allowed"),
            (Regime.NORMAL, 1900.0, 0.7, 1.0, "Recovery to normal - continuity too low (blocked)"),
            (Regime.NORMAL, 1900.0, 0.9, 1.0, "Recovery to normal - continuity OK (allowed)"),

            # Scenario 5: Oscillation detection
            (Regime.HEIGHTENED, 350.0, 1.0, "Normal to heightened (oscillation start)"),
            (Regime.NORMAL, 350.0, 1.0, "Heightened to normal"),
            (Regime.HEIGHTENED, 350.0, 1.0, "Normal to heightened (oscillation continues)"),
            (Regime.NORMAL, 350.0, 1.0, "Heightened to normal (oscillation detected)"),
        ]

        # Reset simulator
        self.__init__()

        results = []
        for scenario in scenarios:
            if len(scenario) == 4:
                proposed, duration, continuity, notes = scenario
            else:
                proposed, duration, continuity, notes = scenario[0], scenario[1], scenario[2], scenario[3]

            step = self.simulate_transition(proposed, duration, continuity, notes)
            results.append(step)

            # Small delay to simulate time passing
            time.sleep(0.01)

        return results

    def print_simulation_results(self, steps: List[SimulationStep]):
        """Print formatted simulation results"""

        print("Nova ORP Transition Simulation: Legal vs Illegal")
        print("=" * 60)

        for i, step in enumerate(steps, 1):
            print(f"\nStep {i}: {step.notes}")
            print(f"  Current: {step.current_regime.value} ({step.duration_in_current:.1f}s)")
            print(f"  Proposed: {step.proposed_regime.value}")
            print(f"  Continuity: {step.continuity_score:.2f}")
            print(f"  Result: {step.result.value}")
            print(f"  Decision: {step.decision.reason}")

            if step.result == TransitionResult.LEGAL_BLOCKED:
                print(f"  Time remaining: {step.decision.time_remaining_s:.1f}s")
            elif step.result == TransitionResult.LEGAL_ALLOWED:
                print("  Transition executed")
            print(f"  Oscillation: {step.decision.oscillation_detected} ({step.decision.oscillation_count} transitions)")

    def get_statistics(self) -> Dict:
        """Get simulation statistics"""
        total = len(self.simulation_steps)
        allowed = sum(1 for s in self.simulation_steps if s.result == TransitionResult.LEGAL_ALLOWED)
        blocked = sum(1 for s in self.simulation_steps if s.result == TransitionResult.LEGAL_BLOCKED)
        forbidden = sum(1 for s in self.simulation_steps if s.result == TransitionResult.ILLEGAL_FORBIDDEN)
        invalid = sum(1 for s in self.simulation_steps if s.result == TransitionResult.ILLEGAL_INVALID)

        return {
            "total_attempts": total,
            "legal_allowed": allowed,
            "legal_blocked": blocked,
            "illegal_forbidden": forbidden,
            "illegal_invalid": invalid,
            "success_rate": allowed / total if total > 0 else 0,
            "hysteresis_effectiveness": blocked / (allowed + blocked) if (allowed + blocked) > 0 else 0
        }

def main():
    simulator = TransitionSimulator()
    steps = simulator.run_simulation_scenarios()
    simulator.print_simulation_results(steps)

    print("\n" + "=" * 60)
    print("SIMULATION STATISTICS:")
    stats = simulator.get_statistics()
    for key, value in stats.items():
        if isinstance(value, float):
            print(f"  {key}: {value:.2f}")
        else:
            print(f"  {key}: {value}")

if __name__ == "__main__":
    main()