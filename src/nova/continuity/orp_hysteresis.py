"""ORP Hysteresis Enforcement - Phase 11.4

Enforces minimum regime durations and blocks rapid oscillation between regimes.
Pure function, reads from ledger, stateless hysteresis logic.

Purpose:
  Prevent rapid regime switches (e.g., NORMAL ↔ HEIGHTENED thrash)
  Enforce minimum regime durations before allowing transitions
  Stabilize recovery ramping to avoid premature exit
  Provide inertia layer for continuity system stability

Canonical Minimum Regime Durations:
  - normal: 60s (1min) - stable baseline requires brief hold
  - heightened: 300s (5min) - prevent premature de-escalation
  - controlled_degradation: 600s (10min) - serious state needs stability
  - emergency_stabilization: 900s (15min) - critical state must persist
  - recovery: 1800s (30min) - gradual recovery requires patience

Critical Constraints:
  - Pure function (reads ledger, no mutation)
  - Blocks transitions ONLY if minimum duration not met
  - Does NOT override MSE/URF/CSI signals (advises, not enforces)
  - Exposes oscillation metrics for observability
  - Synchronizes hysteresis across Governor/Emotion/Slot09
  - Recovery ramping stabilized (prevent early exit)

Hysteresis Algorithm:
  1. Check current regime from ledger
  2. Check duration_s in current regime
  3. If duration_s < MIN_DURATION[regime]: block transition, return current regime
  4. Else: allow transition, return proposed regime
  5. Track oscillation count in last N minutes for metrics
"""

from __future__ import annotations
from typing import Dict, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone


# Canonical minimum regime durations (seconds)
# Format: {regime: min_duration_s}
MIN_REGIME_DURATIONS: Dict[str, float] = {
    "normal": 60.0,                      # 1min - stable baseline
    "heightened": 300.0,                 # 5min - prevent premature de-escalation
    "controlled_degradation": 600.0,     # 10min - serious state needs stability
    "emergency_stabilization": 900.0,    # 15min - critical state must persist
    "recovery": 1800.0,                  # 30min - gradual recovery requires patience
}

# Oscillation detection window (seconds)
OSCILLATION_WINDOW_S = 300.0  # 5 minutes

# Oscillation threshold (transitions per window)
OSCILLATION_THRESHOLD = 3  # More than 3 transitions in 5min = oscillating


@dataclass(frozen=True)
class HysteresisDecision:
    """Result of hysteresis check."""
    allowed: bool                       # True if transition allowed
    effective_regime: str               # Regime to use (current if blocked, proposed if allowed)
    reason: str                         # Human-readable reason
    current_regime: str                 # Current regime from ledger
    current_duration_s: float           # Time in current regime
    min_duration_s: float               # Minimum duration for current regime
    time_remaining_s: float             # Time until minimum duration met (0 if allowed)
    oscillation_detected: bool          # True if rapid oscillation detected
    oscillation_count: int              # Number of transitions in window


def check_regime_hysteresis(
    proposed_regime: str,
    ledger_history: list[Dict],
    current_time: Optional[datetime] = None
) -> HysteresisDecision:
    """Check if regime transition should be allowed based on hysteresis rules.

    Args:
        proposed_regime: Regime being proposed by ORP policy
        ledger_history: List of ledger entries from regime_transition_ledger
                       Format: [{"regime": str, "timestamp": str, "duration_s": float, ...}, ...]
        current_time: Current time (for testing), defaults to now

    Returns:
        HysteresisDecision with allowed flag and effective regime

    Algorithm:
        1. Get current regime from latest ledger entry
        2. If proposed == current: allow (no transition)
        3. Check duration_s in current regime
        4. If duration_s < MIN_DURATION[current]: block, return current regime
        5. Check oscillation metrics
        6. If oscillating: warn but allow (observability, not enforcement)
        7. Else: allow transition, return proposed regime

    Constraints:
        - Pure function (no side effects)
        - Reads ledger, does NOT mutate it
        - Advises on transitions, does NOT enforce (caller decides)

    Examples:
        >>> ledger = [{"regime": "heightened", "timestamp": "2025-01-01T00:00:00Z", "duration_s": 100.0}]
        >>> check_regime_hysteresis("normal", ledger).allowed
        False  # Only 100s in heightened, need 300s
        >>> ledger = [{"regime": "heightened", "timestamp": "2025-01-01T00:00:00Z", "duration_s": 400.0}]
        >>> check_regime_hysteresis("normal", ledger).allowed
        True  # 400s > 300s minimum
    """
    if not ledger_history:
        # No history - allow any regime (bootstrap case)
        return HysteresisDecision(
            allowed=True,
            effective_regime=proposed_regime,
            reason="no_ledger_history",
            current_regime="unknown",
            current_duration_s=0.0,
            min_duration_s=0.0,
            time_remaining_s=0.0,
            oscillation_detected=False,
            oscillation_count=0,
        )

    # Get current regime from latest entry
    latest_entry = ledger_history[-1]
    current_regime = latest_entry.get("regime", "unknown")
    current_duration_s = latest_entry.get("duration_s", 0.0)

    # Normalize regime names
    current_regime_norm = current_regime.lower().strip()
    proposed_regime_norm = proposed_regime.lower().strip()

    # No transition needed
    if current_regime_norm == proposed_regime_norm:
        return HysteresisDecision(
            allowed=True,
            effective_regime=current_regime,
            reason="same_regime_no_transition",
            current_regime=current_regime,
            current_duration_s=current_duration_s,
            min_duration_s=MIN_REGIME_DURATIONS.get(current_regime_norm, 0.0),
            time_remaining_s=0.0,
            oscillation_detected=False,
            oscillation_count=0,
        )

    # Check minimum duration
    min_duration = MIN_REGIME_DURATIONS.get(current_regime_norm, 60.0)  # Default 60s
    time_remaining = max(0.0, min_duration - current_duration_s)

    # Check oscillation metrics
    oscillation_count = _count_oscillations(ledger_history, current_time)
    oscillation_detected = oscillation_count >= OSCILLATION_THRESHOLD

    # Minimum duration not met - block transition
    if current_duration_s < min_duration:
        return HysteresisDecision(
            allowed=False,
            effective_regime=current_regime,  # Stay in current regime
            reason=f"min_duration_not_met:{current_regime_norm}:{current_duration_s:.1f}s<{min_duration:.1f}s",
            current_regime=current_regime,
            current_duration_s=current_duration_s,
            min_duration_s=min_duration,
            time_remaining_s=time_remaining,
            oscillation_detected=oscillation_detected,
            oscillation_count=oscillation_count,
        )

    # Minimum duration met - allow transition
    # (Oscillation detected is advisory, not blocking)
    return HysteresisDecision(
        allowed=True,
        effective_regime=proposed_regime,
        reason=f"min_duration_met:{current_duration_s:.1f}s>={min_duration:.1f}s" +
               (f"|oscillation_detected:{oscillation_count}" if oscillation_detected else ""),
        current_regime=current_regime,
        current_duration_s=current_duration_s,
        min_duration_s=min_duration,
        time_remaining_s=0.0,
        oscillation_detected=oscillation_detected,
        oscillation_count=oscillation_count,
    )


def _count_oscillations(ledger_history: list[Dict], current_time: Optional[datetime] = None) -> int:
    """Count regime transitions in the oscillation window.

    Args:
        ledger_history: List of ledger entries
        current_time: Current time (for testing), defaults to now

    Returns:
        Number of regime transitions in last OSCILLATION_WINDOW_S seconds
    """
    if len(ledger_history) < 2:
        return 0

    # Prefer timezone-aware UTC timestamps to avoid deprecation warnings
    now = current_time or datetime.now(timezone.utc)
    window_start = now - timedelta(seconds=OSCILLATION_WINDOW_S)

    # Filter entries within window
    transitions = 0
    prev_regime = None

    for entry in ledger_history:
        try:
            # Parse timestamp
            timestamp_str = entry.get("timestamp", "")
            if not timestamp_str:
                continue

            # Handle ISO format with 'Z' suffix
            timestamp_str = timestamp_str.replace('Z', '+00:00')
            entry_time = datetime.fromisoformat(timestamp_str)

            # Make window_start timezone-aware if entry_time is
            if entry_time.tzinfo is not None and window_start.tzinfo is None:
                # Make window_start aware (assume UTC)
                window_start = window_start.replace(tzinfo=entry_time.tzinfo)
            elif entry_time.tzinfo is None and window_start.tzinfo is not None:
                # Make entry_time aware (assume UTC)
                entry_time = entry_time.replace(tzinfo=window_start.tzinfo)

            # Skip entries outside window
            if entry_time < window_start:
                prev_regime = entry.get("regime", "")
                continue

            # Count transitions (regime changes)
            current_regime = entry.get("regime", "")
            if prev_regime is not None and current_regime != prev_regime:
                transitions += 1

            prev_regime = current_regime

        except (ValueError, TypeError):
            # Skip entries with bad timestamps
            continue

    return transitions


def get_hysteresis_metrics(ledger_history: list[Dict]) -> Dict[str, any]:
    """Get hysteresis observability metrics.

    Returns:
        {
            "current_regime": str,
            "current_duration_s": float,
            "min_duration_s": float,
            "time_remaining_s": float,
            "oscillation_count": int,
            "oscillation_detected": bool,
            "hysteresis_active": bool,  # True if blocking transitions
        }
    """
    if not ledger_history:
        return {
            "current_regime": "unknown",
            "current_duration_s": 0.0,
            "min_duration_s": 0.0,
            "time_remaining_s": 0.0,
            "oscillation_count": 0,
            "oscillation_detected": False,
            "hysteresis_active": False,
        }

    latest_entry = ledger_history[-1]
    current_regime = latest_entry.get("regime", "unknown")
    current_duration_s = latest_entry.get("duration_s", 0.0)
    min_duration = MIN_REGIME_DURATIONS.get(current_regime.lower().strip(), 60.0)
    time_remaining = max(0.0, min_duration - current_duration_s)
    oscillation_count = _count_oscillations(ledger_history)

    return {
        "current_regime": current_regime,
        "current_duration_s": current_duration_s,
        "min_duration_s": min_duration,
        "time_remaining_s": time_remaining,
        "oscillation_count": oscillation_count,
        "oscillation_detected": oscillation_count >= OSCILLATION_THRESHOLD,
        "hysteresis_active": time_remaining > 0.0,
    }


def stabilize_recovery_ramp(
    proposed_regime: str,
    current_continuity_score: float,
    recovery_threshold: float = 0.85
) -> Tuple[str, str]:
    """Stabilize recovery ramping to prevent premature exit.

    Special logic for recovery regime:
    - Prevent early exit from recovery if continuity not fully restored
    - Block recovery → normal transition unless C > recovery_threshold

    Args:
        proposed_regime: Regime being proposed
        current_continuity_score: Current C (continuity score)
        recovery_threshold: Minimum C to exit recovery (default 0.85)

    Returns:
        (effective_regime, reason) tuple

    Constraints:
        - Only affects recovery → normal transitions
        - Other transitions pass through unchanged
        - Advisory (caller decides whether to enforce)

    Examples:
        >>> stabilize_recovery_ramp("normal", 0.70)  # Current in recovery, C too low
        ("recovery", "recovery_ramp_stabilization:C=0.70<0.85")
        >>> stabilize_recovery_ramp("normal", 0.90)  # C high enough
        ("normal", "recovery_threshold_met:C=0.90>=0.85")
    """
    # Normalize regime
    proposed_norm = proposed_regime.lower().strip()

    # Only stabilize recovery → normal transitions
    # (Caller should only invoke this when current regime is recovery)
    if proposed_norm == "normal":
        if current_continuity_score < recovery_threshold:
            # Block premature exit from recovery
            return (
                "recovery",
                f"recovery_ramp_stabilization:C={current_continuity_score:.2f}<{recovery_threshold:.2f}"
            )
        else:
            # Allow exit from recovery
            return (
                proposed_regime,
                f"recovery_threshold_met:C={current_continuity_score:.2f}>={recovery_threshold:.2f}"
            )

    # Pass through all other transitions
    return (proposed_regime, "no_recovery_stabilization_needed")
