from __future__ import annotations
import time, math
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Any
from .policy import TriPolicy
from .types import Health, RepairDecision
from .detectors import DriftDetector, SurgeDetector
from .repair_planner import RepairPlanner
from .snapshotter import TriSnapshotter
from .safe_mode import SafeMode

@dataclass
class TriMetrics:
    n: int = 0
    mean: float = 0.0
    m2: float = 0.0

    def update(self, x: float):
        self.n += 1
        delta = x - self.mean
        self.mean += delta / self.n
        self.m2 += delta * (x - self.mean)

    @property
    def std(self) -> float:
        return math.sqrt(self.m2 / (self.n - 1)) if self.n > 1 else 0.0

class TriEngine:
    """
    Minimal TRI engine with adaptive recovery & safe mode.
    """
    def __init__(self, model_dir: Path, snapshot_dir: Path, policy: TriPolicy | None = None):
        self.policy = policy or TriPolicy()
        self.metrics = TriMetrics()
        self._alpha_up = self.policy.ema_alpha_up
        self._revert_k = self.policy.revert_k
        self._min_rel = self.policy.min_rel_baseline
        self.threshold = 0.5
        self.baseline = 0.5
        self.safe_mode = SafeMode(
            self.policy.safe_mode_flip_max_s,
            self.policy.safe_mode_max_s
        )
        self.drift = DriftDetector(self.policy.drift_window, self.policy.drift_z_threshold)
        self.surge = SurgeDetector(self.policy.surge_window, self.policy.surge_threshold, self.policy.surge_cooldown_s)
        self.repair = RepairPlanner()
        self.snapshotter = TriSnapshotter(model_dir, snapshot_dir)
        # detector state for assess()
        self._last_drift_z: float = 0.0
        self._surge_events_window: int = 0

    def _tri_score(self, features: Dict[str, float]) -> float:
        # Simple bounded linear score
        s = 0.0
        for k, v in features.items():
            s += 0.1 * float(v)
        return max(0.0, min(1.0, s))

    def observe(self, features: Dict[str, float], *, writes_in_last_sec: int = 0) -> Dict[str, Any]:
        score = self._tri_score(features)
        self.metrics.update(score)
        # label-aware threshold dynamics
        if score > self.threshold:
            # anomaly or strong signal => move up faster
            self.threshold += self._alpha_up * (max(score, self.baseline) - self.threshold)
        else:
            # reversion toward baseline
            self.threshold += self._revert_k * (self.baseline - self.threshold)
        # keep floor relative to baseline and ensure non-negative
        self.threshold = max(0.0, max(self._min_rel * self.baseline, min(0.95, self.threshold)))

        # Update baseline slowly when stable
        self.baseline = 0.9 * self.baseline + 0.1 * score

        # detectors
        evt = self.drift.update(score)
        if evt:
            self._last_drift_z = float(evt.get("z", 0.0))
        surge_evt = self.surge.tick(writes_in_last_sec) if writes_in_last_sec else None
        if surge_evt:
            self._surge_events_window += 1

        return {"score": score, "drift": evt, "surge": surge_evt}

    def assess(self) -> Health:
        return Health(
            drift_z=self._last_drift_z,
            surge_events=self._surge_events_window,
            data_ok=True,
            perf_ok=True,
            tri_mean=self.metrics.mean,
            tri_std=self.metrics.std if self.metrics.n > 1 else self.policy.default_sigma,
            n_samples=self.metrics.n,
        )

    def confidence_interval(self, conf: float = 0.95) -> tuple[float,float]:
        # normal approx
        z = 1.96 if conf >= 0.95 else 1.64
        return (max(0, self.metrics.mean - z*self.metrics.std), min(1, self.metrics.mean + z*self.metrics.std))

    def auto_heal_once(self) -> dict:
        start = time.time()
        h = self.assess()
        # If detectors flagged drift, use it; else fall back to mean-baseline approximation
        if not h.drift_z:
            std = h.tri_std or self.policy.default_sigma
            h.drift_z = abs((self.metrics.mean - self.baseline) / (std + 1e-9))
        # route decision
        dec: RepairDecision = self.repair.decide(h, last_good_id=self.snapshotter.last_good_id())
        ok = True
        if dec.action == "RESTORE_PREV_MODEL" and dec.details.get("snapshot"):
            ok = self.snapshotter.restore(dec.details["snapshot"]) and self.snapshotter.verify_current()
        elif dec.action == "SAFE_MODE_BLOCK":
            self.safe_mode.activate("auto_heal_triggered")
            ok = True
        # record
        self.repair.record_outcome(dec, ok, time.time()-start)
        return {"decision": dec.action, "ok": ok, "dt": time.time()-start}

    def take_snapshot(self):
        return self.snapshotter.take()

    def metrics_snapshot(self) -> dict:
        """Lightweight metrics snapshot for observability and Slot 10 gates."""
        lo, hi = self.confidence_interval(0.95)
        return {
            "tri.mean": self.metrics.mean,
            "tri.std": self.metrics.std,
            "tri.n": self.metrics.n,
            "tri.threshold": self.threshold,
            "tri.baseline": self.baseline,
            "drift.z_last": self._last_drift_z,
            "surge.events_window": self._surge_events_window,
            "safe.active": self.safe_mode.active,
            "ci95.lo": lo, "ci95.hi": hi,
        }