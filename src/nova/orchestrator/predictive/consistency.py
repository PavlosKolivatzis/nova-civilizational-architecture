"""
Multi-Slot Consistency (MSC) — Phase 7 Step 6

Detects cross-slot conflicts where different subsystems signal
contradictory states:

1. Safety ↔ Production: High threat + low pressure → conflict
2. Culture ↔ Deployment: High residual risk + active deployment → conflict
3. Predictive ↔ Production: High collapse risk + open production → conflict

Design:
- Vector-based consistency profile (not scalar)
- Reads slot states via semantic mirror
- Publishes predictive_consistency_gap@1 contract
- Feeds governance gating logic
"""
from dataclasses import dataclass
from typing import Optional


@dataclass
class ConsistencyProfile:
    """
    Multi-slot consistency gap profile.

    Fields:
        gap_score: Composite consistency gap (0..1, higher = worse)
        components: Individual conflict scores by type
        conflicting_slots: List of slot IDs in conflict
        severity: Maximum component conflict (worst-case)
        caused_by: EPD pattern types that contributed to inconsistency
        source_snapshot_hash: Predictive snapshot hash for audit
        timestamp: Profile generation timestamp
    """
    gap_score: float  # 0..1
    components: dict[str, float]
    conflicting_slots: list[str]
    severity: float  # 0..1
    caused_by: list[str]
    source_snapshot_hash: str
    timestamp: float

    def to_dict(self) -> dict:
        """Serialize to contract format."""
        return {
            "score": self.gap_score,
            "components": self.components,
            "conflicting_slots": self.conflicting_slots,
            "severity": self.severity,
            "caused_by": self.caused_by,
            "source_snapshot_hash": self.source_snapshot_hash,
            "timestamp": self.timestamp,
        }


def compute_consistency_gap(
    slot03_state: Optional[dict] = None,
    slot06_state: Optional[dict] = None,
    slot07_state: Optional[dict] = None,
    slot10_state: Optional[dict] = None,
    predictive_snapshot: Optional[dict] = None,
    pattern_alerts: Optional[list] = None,
    timestamp: float = 0.0
) -> ConsistencyProfile:
    """
    Compute multi-slot consistency gap.

    Args:
        slot03_state: Emotional matrix (safety) state
        slot06_state: Cultural synthesis state
        slot07_state: Production controls state
        slot10_state: Deployment state
        predictive_snapshot: Predictive trajectory snapshot
        pattern_alerts: Recent EPD pattern alerts
        timestamp: Current timestamp

    Returns:
        ConsistencyProfile with vector-based gap analysis
    """
    # Default to empty dicts if not provided
    slot03 = slot03_state or {}
    slot06 = slot06_state or {}
    slot07 = slot07_state or {}
    slot10 = slot10_state or {}
    predictive = predictive_snapshot or {}
    alerts = pattern_alerts or []

    components = {}
    conflicting_slots = []

    # Component 1: Safety ↔ Production consistency
    safety_conflict = _compute_safety_production_conflict(slot03, slot07)
    components["safety_production_conflict"] = safety_conflict
    if safety_conflict > 0.3:
        if "slot03" not in conflicting_slots:
            conflicting_slots.append("slot03")
        if "slot07" not in conflicting_slots:
            conflicting_slots.append("slot07")

    # Component 2: Culture ↔ Deployment consistency
    culture_conflict = _compute_culture_deployment_conflict(slot06, slot10)
    components["culture_deployment_conflict"] = culture_conflict
    if culture_conflict > 0.3:
        if "slot06" not in conflicting_slots:
            conflicting_slots.append("slot06")
        if "slot10" not in conflicting_slots:
            conflicting_slots.append("slot10")

    # Component 3: Predictive ↔ Production consistency
    predictive_conflict = _compute_predictive_production_conflict(predictive, slot07)
    components["production_predictive_conflict"] = predictive_conflict
    if predictive_conflict > 0.3:
        if "slot07" not in conflicting_slots:
            conflicting_slots.append("slot07")
        if "predictive" not in conflicting_slots:
            conflicting_slots.append("predictive")

    # Composite gap score (weighted sum)
    gap_score = _clamp(
        0.35 * safety_conflict +
        0.30 * culture_conflict +
        0.35 * predictive_conflict,
        0.0, 1.0
    )

    # Severity = worst component
    severity = max(safety_conflict, culture_conflict, predictive_conflict)

    # Extract pattern types that contributed
    caused_by = [alert.get("type", "") for alert in alerts if alert.get("severity", 0) > 0.5]

    # Get snapshot hash for audit trail
    snapshot_hash = predictive.get("source_snapshot_hash", "unknown")

    return ConsistencyProfile(
        gap_score=gap_score,
        components=components,
        conflicting_slots=sorted(conflicting_slots),
        severity=severity,
        caused_by=caused_by,
        source_snapshot_hash=snapshot_hash,
        timestamp=timestamp
    )


def _compute_safety_production_conflict(slot03: dict, slot07: dict) -> float:
    """
    Safety ↔ Production conflict.

    Pattern: High threat level + low production pressure = conflict
    (system should be cautious but isn't applying backpressure)
    """
    # Extract threat level (normalized 0..1)
    threat_level = slot03.get("threat_level", 0.0)
    if isinstance(threat_level, str):
        # Map categorical to numeric
        threat_map = {"LOW": 0.2, "MEDIUM": 0.5, "HIGH": 0.8, "CRITICAL": 1.0}
        threat_level = threat_map.get(threat_level.upper(), 0.0)

    # Extract pressure (normalized 0..1)
    pressure = slot07.get("pressure_level", 0.0)

    # Conflict when threat is high but pressure is low
    if threat_level >= 0.6 and pressure <= 0.4:
        # Conflict magnitude = threat severity * pressure gap
        conflict = threat_level * 0.7 + (1.0 - pressure) * 0.3
        return _clamp(conflict, 0.0, 1.0)

    return 0.0


def _compute_culture_deployment_conflict(slot06: dict, slot10: dict) -> float:
    """
    Culture ↔ Deployment conflict.

    Pattern: High residual risk + active deployment = conflict
    (deploying despite cultural/ethical concerns)
    """
    # Extract residual risk
    residual_risk = slot06.get("residual_risk", 0.0)

    # Extract deployment phase
    deployment_phase = slot10.get("phase", "idle")
    is_deploying = deployment_phase.lower() in ["deploying", "rolling", "active"]

    # Conflict when high risk + active deployment
    if residual_risk >= 0.5 and is_deploying:
        return _clamp(residual_risk, 0.0, 1.0)

    return 0.0


def _compute_predictive_production_conflict(predictive: dict, slot07: dict) -> float:
    """
    Predictive ↔ Production conflict.

    Pattern: High collapse risk + open production = conflict
    (foresight warns of danger but production gates are open)
    """
    # Extract collapse risk
    collapse_risk = predictive.get("collapse_risk", 0.0)
    collapse_risk = predictive.get("predictive_collapse_risk", collapse_risk)  # Fallback

    # Extract production state
    slot07_mode = slot07.get("mode", "BASELINE")
    slot07_state = slot07.get("state", "closed")
    is_open = slot07_mode.upper() in ["BASELINE", "FULL"] or slot07_state == "open"

    # Conflict when high collapse risk + production open
    if collapse_risk >= 0.6 and is_open:
        return _clamp(collapse_risk, 0.0, 1.0)

    return 0.0


def _clamp(value: float, min_val: float, max_val: float) -> float:
    """Clamp value to [min_val, max_val]."""
    return max(min_val, min(value, max_val))
