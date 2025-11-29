"""Operational Regime Policy (ORP) - Phase 11

Maps continuity signals → operational regimes → slot posture adjustments.
Translates multi-signal risk/stability state into actionable system behavior.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, Any, Optional
from datetime import datetime, timezone, timedelta
from enum import Enum
import logging

logger = logging.getLogger(__name__)

# Phase 11.3: Regime Transition Ledger (optional)
try:
    from src.nova.continuity.regime_transition_ledger import record_regime_transition
except Exception:  # pragma: no cover
    def record_regime_transition(*args, **kwargs) -> Dict[str, Any]:  # type: ignore[misc]
        return {"success": False, "reason": "ledger_not_available"}

# Lazy imports with fallback stubs for continuity signals
try:
    from src.nova.continuity.risk_reconciliation import get_unified_risk_field
except Exception:
    def get_unified_risk_field() -> dict:  # type: ignore[misc]
        return {"composite_risk": 0.0}

try:
    from src.nova.continuity.meta_stability import get_meta_stability_snapshot
except Exception:
    def get_meta_stability_snapshot() -> dict:  # type: ignore[misc]
        return {"meta_instability": 0.0}

try:
    from src.nova.continuity.predictive_foresight import get_predictive_snapshot
except Exception:
    def get_predictive_snapshot() -> dict:  # type: ignore[misc]
        return {"collapse_risk": 0.0}

try:
    from src.nova.continuity.predictive_consistency import get_consistency_gap
except Exception:
    def get_consistency_gap() -> dict:  # type: ignore[misc]
        return {"consistency_gap_score": 0.0}

try:
    from src.nova.continuity.csi_calculator import get_csi_snapshot
except Exception:
    def get_csi_snapshot() -> dict:  # type: ignore[misc]
        return {"continuity_index": 1.0}


def _clamp(value: float, min_val: float = 0.0, max_val: float = 1.0) -> float:
    """Clamp value to [min_val, max_val]."""
    return max(min_val, min(max_val, value))


class Regime(str, Enum):
    """Operational regime classifications."""
    NORMAL = "normal"
    HEIGHTENED = "heightened"
    CONTROLLED_DEGRADATION = "controlled_degradation"
    EMERGENCY_STABILIZATION = "emergency_stabilization"
    RECOVERY = "recovery"


@dataclass
class ContributingFactors:
    """Breakdown of signals contributing to regime score."""
    urf_composite_risk: float = 0.0
    mse_meta_instability: float = 0.0
    predictive_collapse_risk: float = 0.0
    consistency_gap: float = 0.0
    csi_continuity_index: float = 1.0  # Higher is better, will be inverted

    def to_dict(self) -> Dict[str, float]:
        return {
            "urf_composite_risk": self.urf_composite_risk,
            "mse_meta_instability": self.mse_meta_instability,
            "predictive_collapse_risk": self.predictive_collapse_risk,
            "consistency_gap": self.consistency_gap,
            "csi_continuity_index": self.csi_continuity_index,
        }


@dataclass
class PostureAdjustments:
    """Slot behavior modifications for current regime."""
    threshold_multiplier: float = 1.0  # 1.0=normal, <1.0=tighter
    traffic_limit: float = 1.0  # 1.0=100% capacity
    deployment_freeze: bool = False
    safe_mode_forced: bool = False
    monitoring_interval_s: int = 60

    def to_dict(self) -> Dict[str, Any]:
        return {
            "threshold_multiplier": self.threshold_multiplier,
            "traffic_limit": self.traffic_limit,
            "deployment_freeze": self.deployment_freeze,
            "safe_mode_forced": self.safe_mode_forced,
            "monitoring_interval_s": self.monitoring_interval_s,
        }


# Regime thresholds and posture definitions
REGIME_THRESHOLDS = {
    Regime.NORMAL: (0.0, 0.30),
    Regime.HEIGHTENED: (0.30, 0.50),
    Regime.CONTROLLED_DEGRADATION: (0.50, 0.70),
    Regime.EMERGENCY_STABILIZATION: (0.70, 0.85),
    Regime.RECOVERY: (0.85, 1.0),
}

REGIME_POSTURES = {
    Regime.NORMAL: PostureAdjustments(
        threshold_multiplier=1.0,
        traffic_limit=1.0,
        deployment_freeze=False,
        safe_mode_forced=False,
        monitoring_interval_s=60,
    ),
    Regime.HEIGHTENED: PostureAdjustments(
        threshold_multiplier=0.85,
        traffic_limit=0.90,
        deployment_freeze=False,
        safe_mode_forced=False,
        monitoring_interval_s=30,
    ),
    Regime.CONTROLLED_DEGRADATION: PostureAdjustments(
        threshold_multiplier=0.70,
        traffic_limit=0.60,
        deployment_freeze=True,
        safe_mode_forced=False,
        monitoring_interval_s=20,
    ),
    Regime.EMERGENCY_STABILIZATION: PostureAdjustments(
        threshold_multiplier=0.60,
        traffic_limit=0.30,
        deployment_freeze=True,
        safe_mode_forced=True,
        monitoring_interval_s=10,
    ),
    Regime.RECOVERY: PostureAdjustments(
        threshold_multiplier=0.50,
        traffic_limit=0.10,
        deployment_freeze=True,
        safe_mode_forced=True,
        monitoring_interval_s=10,
    ),
}

# Signal weights for regime_score calculation
SIGNAL_WEIGHTS = {
    "urf_composite_risk": 0.30,
    "mse_meta_instability": 0.25,
    "predictive_collapse_risk": 0.20,
    "consistency_gap": 0.15,
    "csi_continuity_index": 0.10,  # Will be inverted
}

# Hysteresis and timing parameters
DOWNGRADE_HYSTERESIS = 0.05  # Score must drop 0.05 below threshold to downgrade
MIN_REGIME_DURATION_S = 300  # 5 minutes minimum before downgrade


@dataclass
class RegimeSnapshot:
    """Complete operational regime state snapshot."""
    regime: Regime
    regime_score: float
    contributing_factors: ContributingFactors
    posture_adjustments: PostureAdjustments
    timestamp: str
    transition_from: Optional[Regime] = None
    time_in_regime_s: float = 0.0  # Phase 16-2: Added for simulator/oracle alignment

    def to_dict(self) -> Dict[str, Any]:
        return {
            "regime": self.regime.value,
            "regime_score": self.regime_score,
            "contributing_factors": self.contributing_factors.to_dict(),
            "posture_adjustments": self.posture_adjustments.to_dict(),
            "timestamp": self.timestamp,
            "transition_from": self.transition_from.value if self.transition_from else None,
            "time_in_regime_s": self.time_in_regime_s,
        }


@dataclass
class ORPState:
    """Public state accessor for ORP internals (Phase 16-2 hardening).
    
    Provides a stable public API for simulator/oracle access instead of
    reaching into private attributes like _current_regime_start.
    """
    current_regime: Regime
    current_regime_start: Optional[datetime]
    time_in_regime_s: float
    last_snapshot: Optional[RegimeSnapshot]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "current_regime": self.current_regime.value,
            "current_regime_start": self.current_regime_start.isoformat() if self.current_regime_start else None,
            "time_in_regime_s": self.time_in_regime_s,
            "last_snapshot": self.last_snapshot.to_dict() if self.last_snapshot else None,
        }


class OperationalRegimePolicy:
    """Manages operational regime classification and posture adjustments."""

    def __init__(
        self,
        downgrade_hysteresis: float = DOWNGRADE_HYSTERESIS,
        min_regime_duration_s: float = MIN_REGIME_DURATION_S,
    ):
        self.downgrade_hysteresis = downgrade_hysteresis
        self.min_regime_duration_s = min_regime_duration_s
        self._current_regime: Regime = Regime.NORMAL
        self._current_regime_start: Optional[datetime] = None
        self._last_snapshot: Optional[RegimeSnapshot] = None

    def compute_regime_score(self, factors: ContributingFactors) -> float:
        """Compute weighted regime score from contributing factors.

        CSI is inverted (lower CSI = higher risk contribution).
        All inputs clamped to [0, 1].
        """
        # Clamp all inputs
        urf = _clamp(factors.urf_composite_risk)
        mse = _clamp(factors.mse_meta_instability)
        pred = _clamp(factors.predictive_collapse_risk)
        gap = _clamp(factors.consistency_gap)
        csi = _clamp(factors.csi_continuity_index)

        # Compute weighted sum with CSI inverted
        score = (
            urf * SIGNAL_WEIGHTS["urf_composite_risk"]
            + mse * SIGNAL_WEIGHTS["mse_meta_instability"]
            + pred * SIGNAL_WEIGHTS["predictive_collapse_risk"]
            + gap * SIGNAL_WEIGHTS["consistency_gap"]
            + (1.0 - csi) * SIGNAL_WEIGHTS["csi_continuity_index"]  # Inverted
        )

        return _clamp(score)

    def classify_regime(
        self,
        regime_score: float,
        current_regime: Regime,
        time_in_regime_s: float,
    ) -> Regime:
        """Classify regime from score with hysteresis and minimum duration.

        Upgrade immediately when score crosses threshold upward.
        Downgrade only if:
          - Score drops below (threshold - hysteresis)
          - AND time_in_regime_s >= min_regime_duration_s
        """
        # Find regime matching score (upgrade case)
        for regime, (low, high) in REGIME_THRESHOLDS.items():
            if low <= regime_score < high:
                target_regime = regime
                break
        else:
            # Score >= 1.0, assign RECOVERY
            target_regime = Regime.RECOVERY

        # Check if upgrade (score increased to higher severity regime)
        regime_order = list(Regime)
        current_idx = regime_order.index(current_regime)
        target_idx = regime_order.index(target_regime)

        if target_idx > current_idx:
            # Upgrade immediately
            return target_regime

        if target_idx < current_idx:
            # Potential downgrade - check hysteresis and duration
            target_upper_threshold = REGIME_THRESHOLDS[target_regime][1]
            hysteresis_threshold = target_upper_threshold - self.downgrade_hysteresis

            if regime_score >= hysteresis_threshold:
                # Not below hysteresis, stay in current regime
                return current_regime

            if time_in_regime_s < self.min_regime_duration_s:
                # Too soon to downgrade, stay in current regime
                return current_regime

            # Downgrade allowed
            return target_regime

        # target_idx == current_idx - no change
        return current_regime

    def evaluate(
        self,
        factors: Optional[ContributingFactors] = None,
        timestamp: Optional[str] = None,
    ) -> RegimeSnapshot:
        """Evaluate current operational regime from live signals.

        If factors not provided, fetches live signals from continuity modules.
        """
        # Fetch live signals if not provided
        if factors is None:
            urf = get_unified_risk_field()
            mse = get_meta_stability_snapshot()
            pred = get_predictive_snapshot()
            gap_data = get_consistency_gap()
            csi = get_csi_snapshot()

            factors = ContributingFactors(
                urf_composite_risk=urf.get("composite_risk", 0.0),
                mse_meta_instability=mse.get("meta_instability", 0.0),
                predictive_collapse_risk=pred.get("collapse_risk", 0.0),
                consistency_gap=gap_data.get("consistency_gap_score", 0.0),
                csi_continuity_index=csi.get("continuity_index", 1.0),
            )

        # Compute regime score
        regime_score = self.compute_regime_score(factors)

        # Calculate time in current regime
        now = datetime.now(timezone.utc)
        if self._current_regime_start is None:
            self._current_regime_start = now
        time_in_regime_s = (now - self._current_regime_start).total_seconds()

        # Classify regime with hysteresis
        previous_regime = self._current_regime
        new_regime = self.classify_regime(regime_score, self._current_regime, time_in_regime_s)

        # Handle regime transition
        transition_from = None
        if new_regime != self._current_regime:
            transition_from = self._current_regime
            self._current_regime = new_regime
            self._current_regime_start = now
            logger.info(
                f"Regime transition: {transition_from.value} → {new_regime.value} "
                f"(score={regime_score:.3f})"
            )

            # Phase 11.3: Record transition in ledger
            record_regime_transition(
                from_regime=transition_from.value,
                to_regime=new_regime.value,
                regime_score=regime_score,
                contributing_factors=factors.__dict__,
                duration_in_previous_s=time_in_regime_s
            )

        # Get posture for new regime
        posture = REGIME_POSTURES[new_regime]

        # Compute final time_in_regime_s for snapshot
        # After transition, time resets to 0; otherwise use computed value
        final_time_in_regime_s = 0.0 if transition_from else time_in_regime_s

        # Create snapshot
        ts = timestamp or now.isoformat()
        snapshot = RegimeSnapshot(
            regime=new_regime,
            regime_score=regime_score,
            contributing_factors=factors,
            posture_adjustments=posture,
            timestamp=ts,
            transition_from=transition_from,
            time_in_regime_s=final_time_in_regime_s,
        )

        self._last_snapshot = snapshot
        return snapshot

    def get_current_regime(self) -> Regime:
        """Get current regime without re-evaluation."""
        return self._current_regime

    def get_last_snapshot(self) -> Optional[RegimeSnapshot]:
        """Get last evaluated snapshot."""
        return self._last_snapshot

    def get_state(self, now: Optional[datetime] = None) -> ORPState:
        """Get current ORP state via public API (Phase 16-2 hardening).
        
        Provides stable accessor for simulator/oracle instead of private attrs.
        
        Args:
            now: Optional timestamp for time_in_regime_s calculation.
                 If None, uses current wall-clock time.
        
        Returns:
            ORPState with current_regime, current_regime_start, time_in_regime_s,
            and last_snapshot.
        """
        if now is None:
            now = datetime.now(timezone.utc)
        
        time_in_regime_s = 0.0
        if self._current_regime_start is not None:
            time_in_regime_s = (now - self._current_regime_start).total_seconds()
        
        return ORPState(
            current_regime=self._current_regime,
            current_regime_start=self._current_regime_start,
            time_in_regime_s=time_in_regime_s,
            last_snapshot=self._last_snapshot,
        )

    def reset(self) -> None:
        """Reset to NORMAL regime (for testing)."""
        self._current_regime = Regime.NORMAL
        self._current_regime_start = None
        self._last_snapshot = None


# ---------- Global Singleton ----------
_GLOBAL_ORP: Optional[OperationalRegimePolicy] = None


def get_orp_engine() -> OperationalRegimePolicy:
    """Get or create global ORP engine."""
    global _GLOBAL_ORP
    if _GLOBAL_ORP is None:
        _GLOBAL_ORP = OperationalRegimePolicy()
    return _GLOBAL_ORP


def get_operational_regime(
    factors: Optional[ContributingFactors] = None,
    timestamp: Optional[str] = None,
) -> Dict[str, Any]:
    """Evaluate and return current operational regime snapshot.

    Main entry point for Governance, Router, Slot10 integration.
    Returns dict for serialization to ledger/metrics.
    """
    engine = get_orp_engine()
    snapshot = engine.evaluate(factors=factors, timestamp=timestamp)
    return snapshot.to_dict()


def get_posture_adjustments() -> Dict[str, Any]:
    """Get current posture adjustments without re-evaluation.

    Lightweight call for slots that need current posture only.
    """
    engine = get_orp_engine()
    snapshot = engine.get_last_snapshot()
    if snapshot is None:
        # No evaluation yet, return NORMAL posture
        return REGIME_POSTURES[Regime.NORMAL].to_dict()
    return snapshot.posture_adjustments.to_dict()


def reset_orp_engine() -> None:
    """Reset global ORP engine to NORMAL (for testing)."""
    global _GLOBAL_ORP
    if _GLOBAL_ORP is not None:
        _GLOBAL_ORP.reset()
    else:
        _GLOBAL_ORP = OperationalRegimePolicy()
