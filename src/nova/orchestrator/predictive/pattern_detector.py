"""
Emergent Pattern Detector (EPD) — Phase 7 Step 5

Stateless detection of deterministic patterns in predictive/governance history:
1. Governance Oscillation: Allow↔Hold toggling > N times in window
2. Predictive Creep: drift_z monotonic increase despite stable coherence
3. Escalation Loop: Router penalties repeated without resolution

Design:
- Stateless entry point (governance maintains debounce state)
- Normalized severity (0..1) for nuanced thresholding
- Deterministic sliding windows (no ML)
- Evidence-based metadata for audit trail
"""
from dataclasses import dataclass
from typing import Optional


@dataclass
class PatternAlert:
    """
    Pattern detection event published to semantic mirror.

    Fields:
        pattern_type: Signature identifier (governance_oscillation, predictive_creep, escalation_loop)
        severity: Normalized 0..1 (higher = more severe)
        window_start: First snapshot timestamp in detection window
        window_end: Last snapshot timestamp in detection window
        metadata: Evidence dict (toggle_count, drift_slope, penalty_repeats, etc.)
    """
    pattern_type: str
    severity: float  # 0..1
    window_start: float
    window_end: float
    metadata: dict


def detect_patterns(
    predictive_history: list[dict],
    governance_history: list[dict],
    router_history: list[dict],
    window_size: int = 20
) -> list[PatternAlert]:
    """
    Detect emergent patterns in recent system history.

    Stateless function; caller (governance) maintains debounce state.

    Args:
        predictive_history: Recent foresight ledger snapshots
        governance_history: Recent governance decisions (allow/hold/block)
        router_history: Recent router decisions with penalties
        window_size: Sliding window size (default 20)

    Returns:
        List of detected pattern alerts (may be empty)
    """
    alerts = []

    # Pattern 1: Governance oscillation (allow/hold toggling)
    if alert := _detect_governance_oscillation(governance_history, window_size):
        alerts.append(alert)

    # Pattern 2: Predictive creep (drift_z monotonic increase)
    if alert := _detect_predictive_creep(predictive_history, window_size):
        alerts.append(alert)

    # Pattern 3: Escalation loop (repeated router penalties)
    if alert := _detect_escalation_loop(router_history, window_size):
        alerts.append(alert)

    return alerts


def _detect_governance_oscillation(
    history: list[dict],
    window_size: int
) -> Optional[PatternAlert]:
    """
    Detect governance oscillation pattern.

    Pattern: Governance decision flips between allow and hold/block
    more than 3 times in the window.

    Severity: (toggle_count - 3) / 7, capped at 1.0
    - 3 toggles => 0.0 (threshold)
    - 5 toggles => 0.29
    - 10 toggles => 1.0 (severe)
    """
    if len(history) < 5:
        return None

    window = history[-window_size:]

    # Extract decision states (allowed: True/False)
    decisions = [
        entry.get("allowed", True)
        for entry in window
        if "allowed" in entry
    ]

    if len(decisions) < 5:
        return None

    # Count state transitions
    toggles = sum(
        1 for i in range(len(decisions) - 1)
        if decisions[i] != decisions[i + 1]
    )

    threshold = 3
    if toggles < threshold:
        return None

    # Normalized severity (0..1)
    severity = min((toggles - threshold) / 7.0, 1.0)

    return PatternAlert(
        pattern_type="governance_oscillation",
        severity=severity,
        window_start=window[0].get("timestamp", 0.0),
        window_end=window[-1].get("timestamp", 0.0),
        metadata={
            "toggle_count": toggles,
            "threshold": threshold,
            "window_size": len(window),
            "decisions": decisions[-10:],  # Last 10 for audit
        }
    )


def _detect_predictive_creep(
    history: list[dict],
    window_size: int
) -> Optional[PatternAlert]:
    """
    Detect predictive creep pattern.

    Pattern: drift_z increases monotonically for ≥5 consecutive
    snapshots while tri_coherence remains above 0.7 (indicates
    uncontrolled epistemic drift despite stable truth signal).

    Severity: drift_velocity / 2.0, capped at 1.0
    - velocity 0.5 => 0.25
    - velocity 1.0 => 0.5
    - velocity ≥2.0 => 1.0 (critical)
    """
    if len(history) < 5:
        return None

    window = history[-window_size:]

    # Extract drift_z and coherence series
    drift_series = []
    for entry in window:
        if "tri_coherence" in entry and "drift_velocity" in entry:
            if entry["tri_coherence"] >= 0.7:  # Only when stable
                drift_series.append({
                    "drift_z": entry.get("tri_drift_z", 0.0),
                    "velocity": entry.get("drift_velocity", 0.0),
                    "timestamp": entry.get("timestamp", 0.0)
                })

    if len(drift_series) < 5:
        return None

    # Check for monotonic increase in last 5 samples
    recent = drift_series[-5:]
    velocities = [s["velocity"] for s in recent]

    # Monotonic: each velocity >= previous
    is_monotonic = all(
        velocities[i] <= velocities[i + 1]
        for i in range(len(velocities) - 1)
    )

    if not is_monotonic or velocities[-1] < 0.1:
        return None

    # Normalized severity based on final velocity
    severity = min(velocities[-1] / 2.0, 1.0)

    return PatternAlert(
        pattern_type="predictive_creep",
        severity=severity,
        window_start=recent[0]["timestamp"],
        window_end=recent[-1]["timestamp"],
        metadata={
            "monotonic_runs": 5,
            "final_velocity": velocities[-1],
            "velocity_delta": velocities[-1] - velocities[0],
            "drift_z_start": recent[0]["drift_z"],
            "drift_z_end": recent[-1]["drift_z"],
        }
    )


def _detect_escalation_loop(
    history: list[dict],
    window_size: int
) -> Optional[PatternAlert]:
    """
    Detect escalation loop pattern.

    Pattern: Router applies penalties to the same route ≥4 times
    in window despite low stability_pressure (< 2.0), indicating
    phantom penalty feedback loop.

    Severity: (penalty_count - 4) / 6, capped at 1.0
    - 4 penalties => 0.0 (threshold)
    - 7 penalties => 0.5
    - 10+ penalties => 1.0 (critical)
    """
    if len(history) < 5:
        return None

    window = history[-window_size:]

    # Extract penalties with low stability pressure (GPT-5.1 robustness refinement)
    penalties = []
    for entry in window:
        penalty = entry.get("penalty", 0.0)
        pressure = entry.get("stability_pressure", float("inf"))

        if penalty > 0.0 and pressure < 2.0:
            penalties.append({
                "route": entry.get("route", "unknown"),
                "penalty": penalty,
                "pressure": pressure,
                "timestamp": entry.get("timestamp", 0.0)
            })

    if len(penalties) < 4:
        return None

    # Count penalties by route (detect if same route penalized repeatedly)
    route_counts = {}
    for p in penalties:
        route = p["route"]
        route_counts[route] = route_counts.get(route, 0) + 1

    # Find route with most penalties
    max_route, max_count = max(route_counts.items(), key=lambda x: x[1])

    threshold = 4
    if max_count < threshold:
        return None

    # Normalized severity
    severity = min((max_count - threshold) / 6.0, 1.0)

    # Calculate averages for affected route
    route_penalties = [p for p in penalties if p["route"] == max_route]
    avg_penalty = sum(p["penalty"] for p in route_penalties) / max_count
    avg_pressure = sum(p["pressure"] for p in route_penalties) / max_count

    return PatternAlert(
        pattern_type="escalation_loop",
        severity=severity,
        window_start=penalties[0]["timestamp"],
        window_end=penalties[-1]["timestamp"],
        metadata={
            "penalty_count": max_count,
            "threshold": threshold,
            "affected_route": max_route,
            "avg_penalty": avg_penalty,
            "avg_pressure": avg_pressure,
        }
    )
