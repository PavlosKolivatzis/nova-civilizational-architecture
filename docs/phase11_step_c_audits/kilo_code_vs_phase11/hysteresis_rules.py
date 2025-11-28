#!/usr/bin/env python3
"""
Nova ORP Hysteresis Rules Articulation
Phase 11 - Hysteresis Decision Contract Implementation
"""

from enum import Enum
from typing import Dict, List, Optional, NamedTuple
from dataclasses import dataclass
from datetime import datetime, timedelta
import json

# Import Regime from state machine module
from regime_state_machine import Regime

@dataclass
class HysteresisDecision:
    allowed: bool
    effective_regime: Regime
    reason: str
    current_regime: Regime
    current_duration_s: float
    min_duration_s: float
    time_remaining_s: float
    oscillation_detected: bool
    oscillation_count: int

    def to_dict(self) -> Dict:
        return {
            "allowed": self.allowed,
            "effective_regime": self.effective_regime.value,
            "reason": self.reason,
            "current_regime": self.current_regime.value,
            "current_duration_s": self.current_duration_s,
            "min_duration_s": self.min_duration_s,
            "time_remaining_s": self.time_remaining_s,
            "oscillation_detected": self.oscillation_detected,
            "oscillation_count": self.oscillation_count
        }

@dataclass
class RegimeTransition:
    timestamp: datetime
    from_regime: Regime
    to_regime: Regime
    duration_s: float

class HysteresisEngine:
    def __init__(self):
        self.min_durations: Dict[Regime, float] = {
            Regime.NORMAL: 60.0,
            Regime.HEIGHTENED: 300.0,
            Regime.CONTROLLED_DEGRADATION: 600.0,
            Regime.EMERGENCY_STABILIZATION: 900.0,
            Regime.RECOVERY: 1800.0
        }

        self.oscillation_window_s = 300.0  # 5 minutes
        self.oscillation_threshold = 3

        # Mock ledger - in real implementation, this would be persistent
        self.transitions: List[RegimeTransition] = []

    def check_regime_hysteresis(self,
                               proposed_regime: Regime,
                               current_regime: Optional[Regime] = None,
                               current_duration_s: float = 0.0,
                               continuity_score: float = 1.0) -> HysteresisDecision:
        """
        Core hysteresis decision logic as per Phase 11 contracts
        """

        # Bootstrap case - no current regime
        if current_regime is None or current_regime == Regime.UNKNOWN:
            return HysteresisDecision(
                allowed=True,
                effective_regime=proposed_regime,
                reason="no_ledger_history",
                current_regime=Regime.UNKNOWN,
                current_duration_s=0.0,
                min_duration_s=0.0,
                time_remaining_s=0.0,
                oscillation_detected=False,
                oscillation_count=0
            )

        # Same regime - no transition needed
        if proposed_regime == current_regime:
            return HysteresisDecision(
                allowed=True,
                effective_regime=current_regime,
                reason="same_regime_no_transition",
                current_regime=current_regime,
                current_duration_s=current_duration_s,
                min_duration_s=self.min_durations[current_regime],
                time_remaining_s=0.0,
                oscillation_detected=False,
                oscillation_count=0
            )

        # Check minimum duration
        min_duration = self.min_durations[current_regime]
        if current_duration_s < min_duration:
            time_remaining = min_duration - current_duration_s
            return HysteresisDecision(
                allowed=False,
                effective_regime=current_regime,
                reason=f"min_duration_not_met:{current_regime.value}:{current_duration_s:.1f}s<{min_duration:.1f}s",
                current_regime=current_regime,
                current_duration_s=current_duration_s,
                min_duration_s=min_duration,
                time_remaining_s=time_remaining,
                oscillation_detected=self._check_oscillation(),
                oscillation_count=self._get_oscillation_count()
            )

        # Check recovery stabilization
        if current_regime == Regime.RECOVERY and proposed_regime == Regime.NORMAL:
            if continuity_score < 0.85:
                return HysteresisDecision(
                    allowed=False,
                    effective_regime=current_regime,
                    reason="recovery_ramp_stabilization",
                    current_regime=current_regime,
                    current_duration_s=current_duration_s,
                    min_duration_s=min_duration,
                    time_remaining_s=0.0,
                    oscillation_detected=self._check_oscillation(),
                    oscillation_count=self._get_oscillation_count()
                )

        # Check oscillation (advisory only)
        oscillation_detected = self._check_oscillation()
        oscillation_count = self._get_oscillation_count()

        # Allow transition
        reason = f"min_duration_met:{current_duration_s:.1f}s>={min_duration:.1f}s"
        if oscillation_detected:
            reason += f"|oscillation_detected:{oscillation_count}"

        return HysteresisDecision(
            allowed=True,
            effective_regime=proposed_regime,
            reason=reason,
            current_regime=current_regime,
            current_duration_s=current_duration_s,
            min_duration_s=min_duration,
            time_remaining_s=0.0,
            oscillation_detected=oscillation_detected,
            oscillation_count=oscillation_count
        )

    def _check_oscillation(self) -> bool:
        """Check if oscillation threshold exceeded in window"""
        return self._get_oscillation_count() >= self.oscillation_threshold

    def _get_oscillation_count(self) -> int:
        """Count transitions in oscillation window"""
        if not self.transitions:
            return 0

        cutoff = datetime.now() - timedelta(seconds=self.oscillation_window_s)
        recent_transitions = [t for t in self.transitions if t.timestamp >= cutoff]
        return len(recent_transitions)

    def record_transition(self, from_regime: Regime, to_regime: Regime, duration_s: float):
        """Record a regime transition in the ledger"""
        transition = RegimeTransition(
            timestamp=datetime.now(),
            from_regime=from_regime,
            to_regime=to_regime,
            duration_s=duration_s
        )
        self.transitions.append(transition)

    def get_recent_transitions(self, window_s: float = 300.0) -> List[RegimeTransition]:
        """Get transitions within time window"""
        cutoff = datetime.now() - timedelta(seconds=window_s)
        return [t for t in self.transitions if t.timestamp >= cutoff]

def articulate_hysteresis_rules():
    """Print articulated hysteresis rules"""
    print("Nova ORP Hysteresis Rules Articulation")
    print("=" * 50)

    print("\n1. DECISION ALGORITHM:")
    print("   Step 1: Check if proposed_regime == current_regime")
    print("           -> Allow (no transition needed)")
    print("   Step 2: Check if current_duration_s < min_duration_s")
    print("           -> Block (hysteresis active)")
    print("   Step 3: Check oscillation count in 5-minute window")
    print("           -> Warn if >= 3 transitions (advisory, not blocking)")
    print("   Step 4: Check recovery stabilization (if recovery -> normal)")
    print("           -> Block if continuity_score < 0.85")
    print("   Step 5: Allow transition if all checks pass")

    print("\n2. MINIMUM DURATIONS:")
    durations = {
        "normal": "60s (1 min)",
        "heightened": "300s (5 min)",
        "controlled_degradation": "600s (10 min)",
        "emergency_stabilization": "900s (15 min)",
        "recovery": "1800s (30 min)"
    }
    for regime, duration in durations.items():
        print(f"   {regime}: {duration}")

    print("\n3. OSCILLATION DETECTION:")
    print("   Window: 300s (5 minutes)")
    print("   Threshold: >=3 transitions")
    print("   Action: Log warning (advisory only)")

    print("\n4. RECOVERY STABILIZATION:")
    print("   Condition: current_regime = recovery AND proposed_regime = normal")
    print("   Check: continuity_score >= 0.85")
    print("   Action: Block if false")

    print("\n5. DECISION REASONS:")
    print("   min_duration_not_met:REGIME:Xs<Ys - Blocked by minimum duration")
    print("   min_duration_met:Xs>=Ys - Allowed after minimum duration")
    print("   same_regime_no_transition - No change needed")
    print("   no_ledger_history - Bootstrap case")
    print("   recovery_ramp_stabilization - Continuity threshold not met")

if __name__ == "__main__":
    articulate_hysteresis_rules()

    print("\n" + "="*50)
    print("EXAMPLE DECISIONS:")

    engine = HysteresisEngine()

    # Example 1: Blocked by minimum duration
    decision1 = engine.check_regime_hysteresis(
        proposed_regime=Regime.NORMAL,
        current_regime=Regime.HEIGHTENED,
        current_duration_s=100.0
    )
    print(f"\n1. Transition blocked (min duration): {decision1.reason}")
    print(f"   Time remaining: {decision1.time_remaining_s:.1f}s")

    # Example 2: Allowed after minimum duration
    decision2 = engine.check_regime_hysteresis(
        proposed_regime=Regime.NORMAL,
        current_regime=Regime.HEIGHTENED,
        current_duration_s=400.0
    )
    print(f"\n2. Transition allowed: {decision2.reason}")

    # Example 3: Same regime
    decision3 = engine.check_regime_hysteresis(
        proposed_regime=Regime.NORMAL,
        current_regime=Regime.NORMAL,
        current_duration_s=120.0
    )
    print(f"\n3. Same regime: {decision3.reason}")

    # Example 4: Recovery stabilization
    decision4 = engine.check_regime_hysteresis(
        proposed_regime=Regime.NORMAL,
        current_regime=Regime.RECOVERY,
        current_duration_s=2000.0,
        continuity_score=0.7
    )
    print(f"\n4. Recovery blocked: {decision4.reason}")