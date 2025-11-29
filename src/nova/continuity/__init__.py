"""Nova Continuity Module - Phase 11+

Provides operational regime policy, verification ledger, and continuity proofs.

Components:
- operational_regime: ORP engine for regime classification
- contract_oracle: Independent ORP implementation for differential testing
- avl_ledger: Autonomous Verification Ledger (Phase 13)
- drift_guard: Drift detection engine (Phase 13)
- continuity_proof: Continuity proof validators (Phase 13)
"""

from src.nova.continuity.operational_regime import (
    Regime,
    ContributingFactors,
    PostureAdjustments,
    RegimeSnapshot,
    ORPState,
    OperationalRegimePolicy,
    get_orp_engine,
    get_operational_regime,
    get_posture_adjustments,
    reset_orp_engine,
    REGIME_THRESHOLDS,
    REGIME_POSTURES,
    SIGNAL_WEIGHTS,
    DOWNGRADE_HYSTERESIS,
    MIN_REGIME_DURATION_S,
)

# Lazy imports for Phase 13 components (may not exist yet)
try:
    from src.nova.continuity.avl_ledger import (
        AVLEntry,
        AVLLedger,
        get_avl_ledger,
        reset_avl_ledger,
        avl_enabled,
        compute_entry_hash,
        compute_entry_id,
        GENESIS_HASH,
    )
except ImportError:
    pass

try:
    from src.nova.continuity.contract_oracle import (
        compute_regime_score_from_contract,
        classify_regime_from_contract,
        compute_and_classify,
    )
except ImportError:
    pass

__all__ = [
    # ORP
    "Regime",
    "ContributingFactors",
    "PostureAdjustments",
    "RegimeSnapshot",
    "ORPState",
    "OperationalRegimePolicy",
    "get_orp_engine",
    "get_operational_regime",
    "get_posture_adjustments",
    "reset_orp_engine",
    "REGIME_THRESHOLDS",
    "REGIME_POSTURES",
    "SIGNAL_WEIGHTS",
    "DOWNGRADE_HYSTERESIS",
    "MIN_REGIME_DURATION_S",
    # AVL (Phase 13)
    "AVLEntry",
    "AVLLedger",
    "get_avl_ledger",
    "reset_avl_ledger",
    "avl_enabled",
    "compute_entry_hash",
    "compute_entry_id",
    "GENESIS_HASH",
    # Contract Oracle
    "compute_regime_score_from_contract",
    "classify_regime_from_contract",
    "compute_and_classify",
]