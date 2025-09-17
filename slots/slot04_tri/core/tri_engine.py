from __future__ import annotations
import time, math, os, tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Any, Union
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
    def __init__(self, model_dir: Union[Path, str, None] = None, snapshot_dir: Union[Path, str, None] = None, policy: TriPolicy | None = None, **kw):
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

        # Handle model and snapshot directories with sensible defaults
        self.model_dir = Path(model_dir) if model_dir else Path(tempfile.mkdtemp(prefix="tri_model_"))
        self.snapshot_dir = Path(snapshot_dir) if snapshot_dir else Path(tempfile.mkdtemp(prefix="tri_snap_"))
        self.snapshotter = TriSnapshotter(self.model_dir, self.snapshot_dir)

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

    def calculate(self, content: str) -> Dict[str, Any]:
        """Calculate TRI score and layer scores for content analysis.

        This method is gated by NOVA_ENABLE_TRI_LINK environment variable.
        Used for integration with Constellation Engine in Slot 5.

        Args:
            content: Text content to analyze

        Returns:
            Dict with "score" and "layer_scores" keys
        """
        flag = os.getenv("NOVA_ENABLE_TRI_LINK", "").strip().lower()
        if flag not in {"1", "true", "yes", "on"}:
            # Return a harmless stub instead of raising to avoid accidental call sites exploding.
            return {
                "score": 0.0,
                "layer_scores": {"structural": 0.0, "semantic": 0.0, "expression": 0.0,
                                 "delta": 0.0, "sigma": 0.0, "theta": 0.0},  # alias keys too
                "metadata": {"disabled": True, "reason": "NOVA_ENABLE_TRI_LINK not enabled"}
            }

        # Simple content analysis to extract features
        features = self._extract_features_from_content(content)

        # Calculate main TRI score
        main_score = max(0.0, min(1.0, self._tri_score(features)))  # clamp for safety

        # Calculate layer-specific scores
        layer_scores = self._calculate_layer_scores(content, features)
        # Provide alias keys expected by other components/tests without breaking your current naming.
        layer_scores = {
            **layer_scores,
            "delta": layer_scores.get("structural", 0.0),
            "sigma": layer_scores.get("semantic", 0.0),
            "theta": layer_scores.get("expression", 0.0)
        }

        return {
            "score": main_score,
            "layer_scores": layer_scores,
            "metadata": {
                "content_length": len(content),
                "feature_count": len(features),
                "method": "tri_layered_analysis",
                "disabled": False
            }
        }

    def _extract_features_from_content(self, content: str) -> Dict[str, float]:
        """Extract features from text content for TRI analysis."""
        words = content.split()
        sentences = content.split('.')

        return {
            "length_factor": min(1.0, len(content) / 1000.0),
            "word_density": len(words) / max(1, len(content)),
            "sentence_complexity": len(sentences) / max(1, len(words)),
            "caps_ratio": sum(1 for c in content if c.isupper()) / max(1, len(content)),
            "punctuation_density": sum(1 for c in content if c in "!?.,;:") / max(1, len(content)),
            "uniqueness": len(set(word.lower() for word in words)) / max(1, len(words))
        }

    def _calculate_layer_scores(self, content: str, features: Dict[str, float]) -> Dict[str, float]:
        """Calculate layer-specific TRI scores for different analysis dimensions."""
        # Layer 1: Structural analysis
        structural_score = (features.get("length_factor", 0) +
                           features.get("sentence_complexity", 0)) / 2

        # Layer 2: Semantic density
        semantic_score = (features.get("word_density", 0) +
                         features.get("uniqueness", 0)) / 2

        # Layer 3: Expression intensity
        expression_score = (features.get("caps_ratio", 0) +
                           features.get("punctuation_density", 0)) / 2

        return {
            "structural": max(0.0, min(1.0, structural_score)),
            "semantic": max(0.0, min(1.0, semantic_score)),
            "expression": max(0.0, min(1.0, expression_score))
        }