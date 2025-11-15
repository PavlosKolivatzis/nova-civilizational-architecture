from __future__ import annotations
from dataclasses import dataclass

@dataclass
class TriPolicy:
    # Recovery / governance
    mttr_target_s: float = 5.0
    safe_mode_flip_max_s: float = 0.5
    safe_mode_max_s: int = 180

    # Drift / anomaly detection
    drift_window: int = 200
    drift_z_threshold: float = 3.0  # z-score trigger
    surge_window: int = 10
    surge_threshold: int = 50
    surge_cooldown_s: float = 0.0

    # Adaptive thresholds (no magic in code)
    ema_alpha_up: float = 0.4
    revert_k: float = 0.6
    min_rel_baseline: float = 0.9

    # Confidence bands
    min_samples_for_confidence: int = 30
    default_sigma: float = 0.15

    # Signing (stubbed in tests)
    signer_key_ref: str = "ed25519://slot4-tri-signing"
