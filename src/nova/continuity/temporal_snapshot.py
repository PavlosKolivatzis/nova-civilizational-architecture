# src/nova/continuity/temporal_snapshot.py

from dataclasses import dataclass, asdict
from typing import Dict, Optional
import time

@dataclass(frozen=True)
class RegimeSnapshot:
    """
    Canonical Phase 13b-compliant regime snapshot.

    This snapshot represents the system state at the moment of potential
    regime transition (PRE-TRANSITION), before the ORP state is updated.

    It is used by:
      • AVL (Autonomous Verification Ledger)
      • Continuity Proofs
      • Drift Guard
      • Trajectory Simulator
      • Regime transition legality evaluation
    """

    # Core regime data
    regime: str                     # current regime (pre-transition)
    previous_regime: str            # regime before transition
    timestamp_s: float              # time of snapshot creation
    time_in_regime_s: float         # time spent in current regime (pre-transition)
    time_in_previous_regime_s: float  # duration of the prior regime

    # Scoring inputs
    regime_score: float
    regime_factors: Dict[str, float]

    # Phase 13b fields
    dual_modality_state: Optional[str] = None
    drift_detected: bool = False
    oracle_classification: Optional[str] = None

    # Ledger linkage (Phase 14+)
    hash_prev: Optional[str] = None

    def to_dict(self) -> Dict:
        """Deterministic dict for ledger or JSON export."""
        return asdict(self)


def make_snapshot(
    regime: str,
    previous_regime: str,
    time_in_regime_s: float,
    time_in_previous_regime_s: float,
    regime_score: float,
    regime_factors: Dict[str, float],
    *,
    dual_modality_state: Optional[str] = None,
    drift_detected: bool = False,
    oracle_classification: Optional[str] = None,
    hash_prev: Optional[str] = None,
    timestamp_s: Optional[float] = None,
) -> RegimeSnapshot:
    """
    Construct a Phase 13b-compliant snapshot.

    NOTE:
      This MUST be called BEFORE the ORP updates its internal regime state.
      This is required for correct dual-modality verification.
    """

    if timestamp_s is None:
        timestamp_s = time.time()

    return RegimeSnapshot(
        regime=regime,
        previous_regime=previous_regime,
        timestamp_s=timestamp_s,
        time_in_regime_s=time_in_regime_s,
        time_in_previous_regime_s=time_in_previous_regime_s,
        regime_score=regime_score,
        regime_factors=regime_factors,
        dual_modality_state=dual_modality_state,
        drift_detected=drift_detected,
        oracle_classification=oracle_classification,
        hash_prev=hash_prev,
    )