#!/usr/bin/env python3
"""
Nova ORP Safety Envelope Violation Detection
Phase 11 - Global Safety Envelope Monitoring
"""

from enum import Enum
from typing import Dict, List, Optional, Callable, Any
from dataclasses import dataclass
from datetime import datetime, timedelta
import json

from regime_state_machine import Regime
from hysteresis_rules import HysteresisEngine

@dataclass
class SafetyViolation:
    rule_id: str
    description: str
    severity: str  # "critical", "warning", "info"
    violated: bool
    details: str
    timestamp: datetime
    context: Dict[str, Any]

class SafetyEnvelopeMonitor:
    def __init__(self):
        self.violations: List[SafetyViolation] = []
        self.hysteresis_engine = HysteresisEngine()

        # Safety envelope rules from nova.operating@1.0.yaml
        self.rules = {
            "no_destructive_oscillation": {
                "description": "No more than 3 regime transitions in any 300s window",
                "severity": "critical",
                "check": self._check_no_destructive_oscillation
            },
            "no_uncontrolled_acceleration": {
                "description": "Learning rate cannot increase during instability",
                "severity": "critical",
                "check": self._check_no_uncontrolled_acceleration
            },
            "no_noise_amplification": {
                "description": "Detection thresholds cannot decrease during instability",
                "severity": "warning",
                "check": self._check_no_noise_amplification
            },
            "amplitude_bounds": {
                "description": "All amplitude multipliers bounded to safe ranges",
                "severity": "critical",
                "check": self._check_amplitude_bounds
            },
            "temporal_inertia": {
                "description": "Children cannot reduce minimum regime durations declared here",
                "severity": "warning",
                "check": self._check_temporal_inertia
            },
            "continuity_preservation": {
                "description": "Continuity score remains within [0,1] at all times",
                "severity": "critical",
                "check": self._check_continuity_preservation
            },
            "recovery_path_guarantee": {
                "description": "Every regime has a defined path back to normal",
                "severity": "info",
                "check": self._check_recovery_path_guarantee
            }
        }

    def check_all_rules(self, context: Dict[str, Any]) -> List[SafetyViolation]:
        """Check all safety envelope rules and return violations"""
        violations = []

        for rule_id, rule_config in self.rules.items():
            violation = self._check_rule(rule_id, rule_config, context)
            if violation.violated:
                violations.append(violation)
                self.violations.append(violation)

        return violations

    def _check_rule(self, rule_id: str, rule_config: Dict, context: Dict[str, Any]) -> SafetyViolation:
        """Check a single safety rule"""
        try:
            violated, details = rule_config["check"](context)
            return SafetyViolation(
                rule_id=rule_id,
                description=rule_config["description"],
                severity=rule_config["severity"],
                violated=violated,
                details=details,
                timestamp=datetime.now(),
                context=context
            )
        except Exception as e:
            return SafetyViolation(
                rule_id=rule_id,
                description=rule_config["description"],
                severity="error",
                violated=True,
                details=f"Rule check failed: {str(e)}",
                timestamp=datetime.now(),
                context=context
            )

    def _check_no_destructive_oscillation(self, context: Dict[str, Any]) -> tuple[bool, str]:
        """Check: count(transitions, window=300s) <= 3"""
        transitions = context.get("recent_transitions", [])
        window_s = 300

        if not transitions:
            return False, "No transitions in window"

        cutoff = datetime.now() - timedelta(seconds=window_s)
        recent_count = sum(1 for t in transitions if t.timestamp >= cutoff)

        violated = recent_count > 3
        details = f"{recent_count} transitions in {window_s}s window (limit: 3)"

        return violated, details

    def _check_no_uncontrolled_acceleration(self, context: Dict[str, Any]) -> tuple[bool, str]:
        """Check: regime.ordinal >= 1 => eta_multiplier <= 1.0"""
        current_regime = context.get("current_regime")
        eta_multiplier = context.get("eta_multiplier", 1.0)

        if not current_regime or current_regime == Regime.UNKNOWN:
            return False, "No current regime"

        # Get regime ordinal (NORMAL=0, HEIGHTENED=1, etc.)
        regime_ordinal = list(Regime).index(current_regime)

        if regime_ordinal >= 1 and eta_multiplier > 1.0:
            return True, f"Regime {current_regime.value} (ordinal {regime_ordinal}) has eta_multiplier {eta_multiplier} > 1.0"

        return False, f"Regime {current_regime.value} eta_multiplier {eta_multiplier} is safe"

    def _check_no_noise_amplification(self, context: Dict[str, Any]) -> tuple[bool, str]:
        """Check: regime.ordinal >= 1 => sensitivity_multiplier >= 1.0"""
        current_regime = context.get("current_regime")
        sensitivity_multiplier = context.get("sensitivity_multiplier", 1.0)

        if not current_regime or current_regime == Regime.UNKNOWN:
            return False, "No current regime"

        regime_ordinal = list(Regime).index(current_regime)

        if regime_ordinal >= 1 and sensitivity_multiplier < 1.0:
            return True, f"Regime {current_regime.value} (ordinal {regime_ordinal}) has sensitivity_multiplier {sensitivity_multiplier} < 1.0"

        return False, f"Regime {current_regime.value} sensitivity_multiplier {sensitivity_multiplier} is safe"

    def _check_amplitude_bounds(self, context: Dict[str, Any]) -> tuple[bool, str]:
        """Check: 0.25 <= eta_scaled <= 1.0 and 0.5 <= emotion <= 1.0 and 1.0 <= sensitivity <= 1.5"""
        eta_scaled = context.get("eta_scaled", 1.0)
        emotion_constriction = context.get("emotion_constriction", 1.0)
        sensitivity_multiplier = context.get("sensitivity_multiplier", 1.0)

        bounds = [
            (0.25, 1.0, eta_scaled, "eta_scaled"),
            (0.5, 1.0, emotion_constriction, "emotion_constriction"),
            (1.0, 1.5, sensitivity_multiplier, "sensitivity_multiplier")
        ]

        violations = []
        for min_val, max_val, actual, name in bounds:
            if not (min_val <= actual <= max_val):
                violations.append(f"{name}={actual:.2f} not in [{min_val}, {max_val}]")

        if violations:
            return True, "; ".join(violations)

        return False, "All amplitude bounds satisfied"

    def _check_temporal_inertia(self, context: Dict[str, Any]) -> tuple[bool, str]:
        """Check: forall child: min_duration_child[regime] >= min_duration_operating[regime]"""
        # This is a meta-rule about child ontologies not reducing durations
        # For simulation, we'll assume compliance unless explicitly violated
        child_durations = context.get("child_min_durations", {})

        operating_durations = self.hysteresis_engine.min_durations

        violations = []
        for regime, operating_duration in operating_durations.items():
            child_duration = child_durations.get(regime, operating_duration)
            if child_duration < operating_duration:
                violations.append(f"{regime.value}: child {child_duration}s < operating {operating_duration}s")

        if violations:
            return True, "; ".join(violations)

        return False, "Temporal inertia preserved"

    def _check_continuity_preservation(self, context: Dict[str, Any]) -> tuple[bool, str]:
        """Check: 0.0 <= csi_value <= 1.0"""
        csi_value = context.get("csi_value", 1.0)

        if not (0.0 <= csi_value <= 1.0):
            return True, f"CSI value {csi_value} not in [0.0, 1.0]"

        return False, f"CSI value {csi_value} is valid"

    def _check_recovery_path_guarantee(self, context: Dict[str, Any]) -> tuple[bool, str]:
        """Check: forall r in regimes: graph.has_path(r, normal)"""
        # For this simulation, check that all regimes except normal have a path back
        # In the actual state machine, this is guaranteed by design
        current_regime = context.get("current_regime")

        if current_regime == Regime.NORMAL:
            return False, "Normal regime is the target"

        # Check if there's a path (simplified check)
        has_path = current_regime in [Regime.HEIGHTENED, Regime.CONTROLLED_DEGRADATION,
                                    Regime.EMERGENCY_STABILIZATION, Regime.RECOVERY]

        if not has_path:
            return True, f"No recovery path defined for {current_regime.value}"

        return False, f"Recovery path exists for {current_regime.value}"

    def simulate_violations(self) -> List[SafetyViolation]:
        """Run simulation scenarios that trigger safety violations"""

        scenarios = [
            # Normal operation - should pass all checks
            {
                "current_regime": Regime.NORMAL,
                "eta_multiplier": 1.0,
                "sensitivity_multiplier": 1.0,
                "eta_scaled": 0.8,
                "emotion_constriction": 1.0,
                "sensitivity_multiplier": 1.0,
                "csi_value": 0.95,
                "recent_transitions": []
            },

            # Uncontrolled acceleration violation
            {
                "current_regime": Regime.HEIGHTENED,
                "eta_multiplier": 1.5,  # Should be <= 1.0
                "sensitivity_multiplier": 1.2,
                "eta_scaled": 0.9,
                "emotion_constriction": 0.95,
                "csi_value": 0.8,
                "recent_transitions": []
            },

            # Noise amplification violation
            {
                "current_regime": Regime.EMERGENCY_STABILIZATION,
                "eta_multiplier": 0.5,
                "sensitivity_multiplier": 0.8,  # Should be >= 1.0
                "eta_scaled": 0.3,
                "emotion_constriction": 0.6,
                "csi_value": 0.3,
                "recent_transitions": []
            },

            # Amplitude bounds violation
            {
                "current_regime": Regime.RECOVERY,
                "eta_multiplier": 0.25,
                "sensitivity_multiplier": 1.8,  # Should be <= 1.5
                "eta_scaled": 0.1,  # Should be >= 0.25
                "emotion_constriction": 0.3,  # Should be >= 0.5
                "csi_value": 0.9,
                "recent_transitions": []
            },

            # Continuity violation
            {
                "current_regime": Regime.EMERGENCY_STABILIZATION,
                "eta_multiplier": 0.5,
                "sensitivity_multiplier": 1.5,
                "eta_scaled": 0.25,
                "emotion_constriction": 0.5,
                "csi_value": -0.1,  # Invalid
                "recent_transitions": []
            },

            # Destructive oscillation
            {
                "current_regime": Regime.HEIGHTENED,
                "eta_multiplier": 0.9,
                "sensitivity_multiplier": 1.1,
                "eta_scaled": 0.8,
                "emotion_constriction": 0.9,
                "csi_value": 0.7,
                "recent_transitions": [
                    type('Transition', (), {'timestamp': datetime.now() - timedelta(seconds=i*50)})()
                    for i in range(5)  # 5 transitions in 250s
                ]
            }
        ]

        all_violations = []
        for scenario in scenarios:
            violations = self.check_all_rules(scenario)
            all_violations.extend(violations)

        return all_violations

def main():
    monitor = SafetyEnvelopeMonitor()
    violations = monitor.simulate_violations()

    print("Nova ORP Safety Envelope Violation Detection")
    print("=" * 50)

    if not violations:
        print("No violations detected in simulation.")
        return

    print(f"Detected {len(violations)} safety envelope violations:\n")

    for i, violation in enumerate(violations, 1):
        print(f"{i}. {violation.rule_id} ({violation.severity.upper()})")
        print(f"   Description: {violation.description}")
        print(f"   Details: {violation.details}")
        print(f"   Context: {violation.context}")
        print()

    # Summary by severity
    severity_counts = {}
    for v in violations:
        severity_counts[v.severity] = severity_counts.get(v.severity, 0) + 1

    print("VIOLATION SUMMARY:")
    for severity, count in severity_counts.items():
        print(f"  {severity.upper()}: {count}")

if __name__ == "__main__":
    main()