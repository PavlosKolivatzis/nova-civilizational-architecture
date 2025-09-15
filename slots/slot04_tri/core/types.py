from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, Any, Literal

RepairAction = Literal["RESTORE_PREV_MODEL","REWEIGHT_CALIBRATION","SEMANTIC_PATCH","SAFE_MODE_BLOCK","NOOP"]

@dataclass
class Health:
    drift_z: float
    surge_events: int
    data_ok: bool
    perf_ok: bool
    tri_mean: float
    tri_std: float
    n_samples: int

@dataclass
class RepairDecision:
    action: RepairAction
    reason: str
    details: Dict[str, Any]
    confidence: float = 0.7
    estimated_time_s: float = 1.5