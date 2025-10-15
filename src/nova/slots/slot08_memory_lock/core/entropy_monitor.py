"""Schema drift detection and entropy monitoring for adaptive threat detection."""

import hashlib
import json
import time
from collections import defaultdict, deque
from statistics import mean, stdev
from typing import Any, Deque, DefaultDict, Dict, Optional

from .policy import Slot8Policy


class EntropyMonitor:
    """Monitors schema drift and data entropy for anomaly detection."""

    def __init__(self, window_size: int = 50, entropy_threshold: float = 0.8,
                 policy: Optional[Slot8Policy] = None):
        """Initialize entropy monitor with sliding window."""
        self.window_size = window_size
        self.entropy_threshold = entropy_threshold
        self.policy = policy or Slot8Policy()

        # Sliding windows for different metrics
        self.schema_hashes: Deque[str] = deque(maxlen=window_size)
        self.content_sizes: Deque[int] = deque(maxlen=window_size)
        self.operation_types: Deque[str] = deque(maxlen=window_size)
        self.timestamps: Deque[float] = deque(maxlen=window_size)

        # Pattern tracking
        self.schema_patterns: DefaultDict[str, int] = defaultdict(int)
        self.size_patterns: DefaultDict[str, int] = defaultdict(int)
        self.operation_patterns: DefaultDict[str, int] = defaultdict(int)

        # Adaptive thresholds
        self.adaptive_entropy_threshold: float = entropy_threshold
        self.baseline_entropy: float = 0.0
        self.anomaly_count: int = 0
        self._baseline_seen: int = 0
        self._frozen_baseline_threshold: Optional[float] = None  # set after enough baseline samples

    def update(self, obj: Any, operation_type: str = "unknown") -> float:
        """Update entropy monitor with new object and return entropy score."""
        current_time = time.time()

        # Calculate schema hash
        schema_hash = self._calculate_schema_hash(obj)
        content_size = self._calculate_content_size(obj)

        # Update sliding windows
        self.schema_hashes.append(schema_hash)
        self.content_sizes.append(content_size)
        self.operation_types.append(operation_type)
        self.timestamps.append(current_time)

        # Update pattern tracking
        self.schema_patterns[schema_hash] += 1
        self.size_patterns[self._size_bucket(content_size)] += 1
        self.operation_patterns[operation_type] += 1

        # Calculate current entropy
        entropy_score = self._calculate_entropy_score()

        # Update adaptive threshold
        self._update_adaptive_threshold(entropy_score, operation_type)

        return entropy_score

    def _calculate_schema_hash(self, obj: Any) -> str:
        """Calculate hash representing the schema/structure of an object."""
        def normalize_schema(x):
            """Recursively normalize object to extract schema."""
            if isinstance(x, dict):
                return {k: normalize_schema(v) for k, v in sorted(x.items())}
            elif isinstance(x, (list, tuple)):
                # For collections, take schema of first few elements
                samples = x[:3] if len(x) > 3 else x
                return [normalize_schema(item) for item in samples]
            elif isinstance(x, (int, float)):
                return "number"
            elif isinstance(x, str):
                return "string"
            elif isinstance(x, bool):
                return "boolean"
            elif x is None:
                return "null"
            else:
                return type(x).__name__

        normalized = normalize_schema(obj)
        schema_json = json.dumps(normalized, sort_keys=True)
        return hashlib.sha256(schema_json.encode()).hexdigest()[:16]

    def _calculate_content_size(self, obj: Any) -> int:
        """Calculate approximate content size of object."""
        try:
            if isinstance(obj, (str, bytes)):
                return len(obj)
            elif isinstance(obj, dict):
                return sum(len(str(k)) + self._calculate_content_size(v) for k, v in obj.items())
            elif isinstance(obj, (list, tuple)):
                return sum(self._calculate_content_size(item) for item in obj)
            else:
                return len(str(obj))
        except Exception:
            return 0

    def _size_bucket(self, size: int) -> str:
        """Bucket content sizes for pattern analysis."""
        if size < 100:
            return "small"
        elif size < 1000:
            return "medium"
        elif size < 10000:
            return "large"
        else:
            return "xlarge"

    def _calculate_entropy_score(self) -> float:
        """Calculate current entropy score based on schema diversity."""
        if len(self.schema_hashes) < 2:
            return 0.0

        # Schema diversity entropy
        unique_schemas = len(set(self.schema_hashes))
        total_schemas = len(self.schema_hashes)
        schema_entropy = unique_schemas / total_schemas

        # Size variance entropy
        if len(self.content_sizes) > 1:
            size_variance = stdev(self.content_sizes) / max(1, mean(self.content_sizes))
            size_entropy = min(1.0, size_variance)
        else:
            size_entropy = 0.0

        # Operation diversity entropy
        unique_operations = len(set(self.operation_types))
        operation_entropy = unique_operations / max(1, len(self.operation_types))

        # Temporal entropy (rate of change)
        if len(self.timestamps) >= 3:  # need ≥3 points to form ≥2 deltas
            time_deltas = [self.timestamps[i] - self.timestamps[i-1]
                           for i in range(1, len(self.timestamps))]
            # Guard: require ≥2 deltas for stdev; ignore non-positive deltas
            time_deltas = [dt for dt in time_deltas if dt > 0]
            if len(time_deltas) >= 2:
                temporal_variance = stdev(time_deltas) / max(0.1, mean(time_deltas))
                temporal_entropy = min(1.0, temporal_variance / 10.0)  # normalize
            else:
                temporal_entropy = 0.0
        else:
            temporal_entropy = 0.0

        # Weighted combination
        combined_entropy = (
            schema_entropy * 0.4 +
            size_entropy * 0.2 +
            operation_entropy * 0.2 +
            temporal_entropy * 0.2
        )

        return min(1.0, combined_entropy)

    def _update_adaptive_threshold(self, current_entropy: float, context: str = "unknown"):
        """Update adaptive entropy threshold with context-aware mean-reversion."""
        if len(self.schema_hashes) < 5:
            return  # Need some data for meaningful adaptation

        obs = current_entropy
        theta = self.adaptive_entropy_threshold

        # 1) capture a stable baseline from early "baseline" samples
        if context == "baseline":
            self._baseline_seen += 1
            # freeze after enough samples so it's not noisy
            if self._baseline_seen == 10 and self._frozen_baseline_threshold is None:
                self._frozen_baseline_threshold = theta

        # 2) adapt + mean-revert
        # reactive step - use policy parameters instead of magic numbers
        if context == "anomaly":
            alpha = self.policy.entropy_alpha_up  # Fast adaptation during anomalies
            self.anomaly_count += 1
        else:
            alpha = 0.10  # slower during normal/baseline

        theta = (1 - alpha) * theta + alpha * obs

        # mean-revert toward frozen baseline only when data is normal/baseline
        if context in ("normal", "baseline") and self._frozen_baseline_threshold is not None:
            beta = self.policy.entropy_k_revert  # Reversion strength from policy
            theta = (1 - beta) * theta + beta * self._frozen_baseline_threshold

            # Optional safety: prevent drift below baseline
            min_threshold = self.policy.entropy_min_rel_baseline * self._frozen_baseline_threshold
            theta = max(min_threshold, theta)

        # clamp
        self.adaptive_entropy_threshold = max(0.05, min(0.95, theta))

    def is_anomalous(self, entropy_score: Optional[float] = None) -> bool:
        """Check if current or provided entropy score indicates anomaly."""
        if entropy_score is None:
            entropy_score = self._calculate_entropy_score()

        return entropy_score > self.adaptive_entropy_threshold

    def get_metrics(self) -> Dict[str, Any]:
        """Get comprehensive entropy monitoring metrics."""
        current_entropy = self._calculate_entropy_score()

        metrics: Dict[str, Any] = {
            "current_entropy": current_entropy,
            "adaptive_threshold": self.adaptive_entropy_threshold,
            "baseline_entropy": self.baseline_entropy,
            "is_anomalous": self.is_anomalous(current_entropy),
            "window_size": len(self.schema_hashes),
            "unique_schemas": len(set(self.schema_hashes)),
            "anomaly_count": self.anomaly_count,
            "window_full": len(self.schema_hashes) == self.window_size
        }

        # Pattern analysis
        if self.schema_hashes:
            metrics["schema_diversity"] = len(set(self.schema_hashes)) / len(self.schema_hashes)

        if self.content_sizes:
            size_stats: Dict[str, float] = {
                "min": min(self.content_sizes),
                "max": max(self.content_sizes),
                "mean": mean(self.content_sizes),
                "variance": stdev(self.content_sizes) if len(self.content_sizes) > 1 else 0.0
            }
            metrics["size_stats"] = size_stats

        # Operation pattern analysis
        if self.operation_types:
            operation_counts: DefaultDict[str, int] = defaultdict(int)
            for op in self.operation_types:
                operation_counts[op] += 1
            metrics["operation_distribution"] = dict(operation_counts)

        return metrics

    def reset(self):
        """Reset entropy monitor to initial state."""
        self.schema_hashes.clear()
        self.content_sizes.clear()
        self.operation_types.clear()
        self.timestamps.clear()
        self.schema_patterns.clear()
        self.size_patterns.clear()
        self.operation_patterns.clear()
        self.adaptive_entropy_threshold = self.entropy_threshold
        self.baseline_entropy = 0.0
        self.anomaly_count = 0

    def get_pattern_analysis(self) -> Dict[str, Any]:
        """Get detailed pattern analysis for forensics."""
        analysis = {
            "most_common_schemas": [],
            "most_common_sizes": [],
            "most_common_operations": [],
            "pattern_stability": 0.0
        }

        # Most common patterns
        if self.schema_patterns:
            sorted_schemas = sorted(self.schema_patterns.items(), key=lambda x: x[1], reverse=True)
            analysis["most_common_schemas"] = sorted_schemas[:5]

        if self.size_patterns:
            sorted_sizes = sorted(self.size_patterns.items(), key=lambda x: x[1], reverse=True)
            analysis["most_common_sizes"] = sorted_sizes[:5]

        if self.operation_patterns:
            sorted_ops = sorted(self.operation_patterns.items(), key=lambda x: x[1], reverse=True)
            analysis["most_common_operations"] = sorted_ops[:5]

        # Pattern stability (how consistent are the patterns)
        if len(self.schema_hashes) > 0:
            len(self.schema_patterns)
            max_pattern_count = max(self.schema_patterns.values()) if self.schema_patterns else 0
            analysis["pattern_stability"] = max_pattern_count / max(1, len(self.schema_hashes))

        return analysis
