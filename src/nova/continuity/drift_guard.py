"""Drift Guard - Phase 13

Real-time detection of ORP implementation divergence from contract oracle.
Detects dual-modality disagreement, invariant violations, and amplitude bounds violations.

Design: ADR-13-Init.md
"""

from __future__ import annotations
import logging
import os
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

from src.nova.continuity.avl_ledger import AVLEntry

logger = logging.getLogger(__name__)

# Drift detection thresholds
SCORE_DRIFT_THRESHOLD = 1e-6  # Maximum allowed score difference
AMPLITUDE_BOUNDS = {
    "threshold_multiplier": (0.5, 2.0),
    "traffic_limit": (0.0, 1.0),
}


@dataclass
class DriftResult:
    """Result of drift detection check."""
    drift_detected: bool
    reasons: List[str]
    entry: AVLEntry
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "drift_detected": self.drift_detected,
            "reasons": self.reasons,
            "entry_id": self.entry.entry_id,
            "timestamp": self.entry.timestamp,
        }


class DriftGuard:
    """Drift detection engine.
    
    Detects divergence between ORP implementation and contract oracle.
    Can optionally halt transitions on drift detection.
    """
    
    def __init__(
        self,
        halt_on_drift: bool = False,
        score_drift_threshold: float = SCORE_DRIFT_THRESHOLD,
        amplitude_bounds: Optional[Dict[str, Tuple[float, float]]] = None,
        enabled: bool = True,
    ):
        """Initialize drift guard.
        
        Args:
            halt_on_drift: If True, raise exception on drift detection
            score_drift_threshold: Maximum allowed score difference (default 1e-6)
            amplitude_bounds: Bounds for amplitude parameters
            enabled: If False, check() always returns no drift
        """
        self._halt_on_drift = halt_on_drift
        self._score_drift_threshold = score_drift_threshold
        self._amplitude_bounds = amplitude_bounds or AMPLITUDE_BOUNDS
        self._enabled = enabled
        
        # Load from environment
        if os.environ.get("NOVA_AVL_HALT_ON_DRIFT", "0") == "1":
            self._halt_on_drift = True
    
    def configure(
        self,
        halt_on_drift: Optional[bool] = None,
        score_drift_threshold: Optional[float] = None,
        enabled: Optional[bool] = None,
    ) -> None:
        """Configure drift guard settings.
        
        Args:
            halt_on_drift: If True, raise exception on drift detection
            score_drift_threshold: Maximum allowed score difference
            enabled: If False, check() always returns no drift
        """
        if halt_on_drift is not None:
            self._halt_on_drift = halt_on_drift
        if score_drift_threshold is not None:
            self._score_drift_threshold = score_drift_threshold
        if enabled is not None:
            self._enabled = enabled
    
    def check(self, entry: AVLEntry) -> Tuple[bool, List[str]]:
        """Check entry for drift.
        
        Detects:
        1. Dual-modality disagreement (ORP ≠ oracle regime)
        2. Score computation drift (|ORP_score - oracle_score| > threshold)
        3. Invariant violations (hysteresis, min-duration, ledger continuity, amplitude)
        4. Amplitude bounds exceeded
        
        Args:
            entry: AVLEntry to check
        
        Returns:
            Tuple of (drift_detected, list of reason strings)
        
        Raises:
            DriftDetectedError: If halt_on_drift=True and drift detected
        """
        if not self._enabled:
            return False, []
        
        reasons: List[str] = []
        
        # 1. Dual-modality disagreement
        if entry.orp_regime != entry.oracle_regime:
            reasons.append(
                f"Dual-modality disagreement: ORP={entry.orp_regime} vs Oracle={entry.oracle_regime}"
            )
        
        # 2. Score computation drift
        score_diff = abs(entry.orp_regime_score - entry.oracle_regime_score)
        if score_diff > self._score_drift_threshold:
            reasons.append(
                f"Score drift: ORP={entry.orp_regime_score:.6f} vs "
                f"Oracle={entry.oracle_regime_score:.6f} (diff={score_diff:.6f})"
            )
        
        # 3. Invariant violations
        invariant_violations = self._check_invariants(entry)
        reasons.extend(invariant_violations)
        
        # 4. Amplitude bounds
        amplitude_violations = self._check_amplitude_bounds(entry)
        reasons.extend(amplitude_violations)
        
        drift_detected = len(reasons) > 0
        
        if drift_detected:
            logger.warning(
                f"Drift detected at {entry.timestamp}: {reasons}"
            )
            
            if self._halt_on_drift:
                raise DriftDetectedError(reasons, entry)
        
        return drift_detected, reasons
    
    def _check_invariants(self, entry: AVLEntry) -> List[str]:
        """Check invariant flags in entry.
        
        Returns list of violation messages.
        """
        violations = []
        
        if not entry.hysteresis_enforced:
            violations.append("Invariant violation: hysteresis not enforced")
        
        if not entry.min_duration_enforced:
            violations.append("Invariant violation: min-duration not enforced")
        
        if not entry.ledger_continuity:
            violations.append("Invariant violation: ledger continuity broken")
        
        if not entry.amplitude_valid:
            violations.append("Invariant violation: amplitude invalid")
        
        return violations
    
    def _check_amplitude_bounds(self, entry: AVLEntry) -> List[str]:
        """Check amplitude parameters are within bounds.
        
        Returns list of violation messages.
        """
        violations = []
        posture = entry.posture_adjustments
        
        # Check threshold_multiplier
        if "threshold_multiplier" in posture:
            mult = posture["threshold_multiplier"]
            low, high = self._amplitude_bounds["threshold_multiplier"]
            if not (low <= mult <= high):
                violations.append(
                    f"Amplitude out of bounds: threshold_multiplier={mult} "
                    f"(expected [{low}, {high}])"
                )
        
        # Check traffic_limit
        if "traffic_limit" in posture:
            limit = posture["traffic_limit"]
            low, high = self._amplitude_bounds["traffic_limit"]
            if not (low <= limit <= high):
                violations.append(
                    f"Amplitude out of bounds: traffic_limit={limit} "
                    f"(expected [{low}, {high}])"
                )
        
        return violations
    
    def check_and_update(self, entry: AVLEntry) -> AVLEntry:
        """Check entry for drift and update its drift fields.
        
        Convenience method that checks and updates entry in place.
        
        Args:
            entry: AVLEntry to check and update
        
        Returns:
            Updated entry with drift_detected and drift_reasons set
        """
        drift_detected, reasons = self.check(entry)
        entry.drift_detected = drift_detected
        entry.drift_reasons = reasons
        entry.dual_modality_agreement = (entry.orp_regime == entry.oracle_regime)
        return entry
    
    @property
    def halt_on_drift(self) -> bool:
        """Get halt_on_drift setting."""
        return self._halt_on_drift
    
    @property
    def enabled(self) -> bool:
        """Get enabled setting."""
        return self._enabled
    
    @property
    def score_drift_threshold(self) -> float:
        """Get score drift threshold."""
        return self._score_drift_threshold


class DriftDetectedError(Exception):
    """Exception raised when drift is detected and halt_on_drift=True."""
    
    def __init__(self, reasons: List[str], entry: AVLEntry):
        self.reasons = reasons
        self.entry = entry
        super().__init__(f"Drift detected: {reasons}")


# ---------- Global Singleton ----------
_GLOBAL_DRIFT_GUARD: Optional[DriftGuard] = None


def get_drift_guard() -> DriftGuard:
    """Get or create global drift guard instance."""
    global _GLOBAL_DRIFT_GUARD
    if _GLOBAL_DRIFT_GUARD is None:
        _GLOBAL_DRIFT_GUARD = DriftGuard()
    return _GLOBAL_DRIFT_GUARD


def reset_drift_guard() -> None:
    """Reset global drift guard (for testing)."""
    global _GLOBAL_DRIFT_GUARD
    _GLOBAL_DRIFT_GUARD = None