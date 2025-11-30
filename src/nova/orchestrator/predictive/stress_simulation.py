"""
Stress Simulation Framework — Phase 7.0-RC

Validates system auto-recovery from controlled drift/jitter injection.

Injection targets:
- Predictive drift (via PTE input domain)
- Temporal jitter (variance spikes)
- Combined escalation cascades

Recovery criteria:
- RIS ≥ 0.90 within 24h
- Memory stability ≥ 0.80 within 24h
- Recovery rate ≥ 0.90 (normalized)

Feature flag: NOVA_ENABLE_STRESS_TEST (default: false)
Safety: Sandboxed to test mode only
"""

from __future__ import annotations

import time
import os
from dataclasses import dataclass
from typing import Optional, Literal

from nova.orchestrator.temporal.engine import TemporalSnapshot

try:  # pragma: no cover - semantic mirror optional
    from nova.orchestrator.semantic_mirror import publish as mirror_publish
except Exception:  # pragma: no cover
    mirror_publish = None  # type: ignore[assignment]


StressMode = Literal["drift", "jitter", "combined", "none"]


@dataclass
class StressState:
    """Current stress injection state."""
    mode: StressMode
    injection_active: bool
    injection_tick: int
    magnitude: float
    collapse_risk: float
    ris: float
    memory_stability: float
    timestamp: float


@dataclass
class RecoveryMetrics:
    """Recovery tracking metrics."""
    baseline_ris: float
    baseline_stability: float
    min_ris: float
    min_stability: float
    final_ris: float
    final_stability: float
    recovery_ticks: int
    recovered: bool
    recovery_rate: float


class StressSimulator:
    """
    Stress simulation framework for predictive resilience testing.

    Injects controlled anomalies into Temporal Ledger to stress:
    - Predictive Trajectory Engine (drift signals)
    - Memory Resonance Window (jitter/variance)
    - RIS composite trust metric

    Measures 24h recovery to validate RC criteria.
    """

    def __init__(self):
        """Initialize stress simulator."""
        self._stress_state = StressState(
            mode="none",
            injection_active=False,
            injection_tick=0,
            magnitude=0.0,
            collapse_risk=0.0,
            ris=0.0,
            memory_stability=0.0,
            timestamp=time.time()
        )
        self._baseline_ris: Optional[float] = None
        self._baseline_stability: Optional[float] = None
        self._min_ris: float = 1.0
        self._min_stability: float = 1.0
        self._recovery_samples: list[tuple[float, float]] = []  # (ris, stability)

    def is_enabled(self) -> bool:
        """Check if stress testing is enabled via feature flag."""
        return os.getenv("NOVA_ENABLE_STRESS_TEST", "false").lower() == "true"

    def inject_drift_anomaly(
        self,
        baseline_snapshot: TemporalSnapshot,
        magnitude: float = 0.2,
        duration_ticks: int = 10
    ) -> list[TemporalSnapshot]:
        """
        Inject predictive drift anomaly into Temporal Ledger.

        Creates synthetic snapshots with elevated drift signals:
        - drift_velocity increased
        - drift_acceleration increased
        - tri_coherence reduced
        - convergence_score reduced

        Args:
            baseline_snapshot: Baseline temporal snapshot
            magnitude: Drift magnitude [0.0, 1.0] (0.2 = +20% drift)
            duration_ticks: Number of ticks to sustain drift

        Returns:
            list[TemporalSnapshot]: Synthetic snapshots for injection
        """
        if not self.is_enabled():
            return []

        self._stress_state.mode = "drift"
        self._stress_state.injection_active = True
        self._stress_state.magnitude = magnitude

        synthetic_snapshots = []
        for tick in range(duration_ticks):
            # Elevate drift signals
            snapshot = TemporalSnapshot(
                timestamp=time.time() + tick,
                tri_coherence=max(0.0, baseline_snapshot.tri_coherence - magnitude * 0.3),
                tri_drift_z=baseline_snapshot.tri_drift_z + magnitude,
                slot07_mode=baseline_snapshot.slot07_mode,
                gate_state=baseline_snapshot.gate_state,
                governance_state=baseline_snapshot.governance_state,
                prediction_error=baseline_snapshot.prediction_error + magnitude * 0.5,
                temporal_drift=baseline_snapshot.temporal_drift + magnitude,
                temporal_variance=baseline_snapshot.temporal_variance + magnitude * 0.2,
                convergence_score=max(0.0, baseline_snapshot.convergence_score - magnitude),
                divergence_penalty=baseline_snapshot.divergence_penalty + magnitude
            )
            synthetic_snapshots.append(snapshot)
            self._stress_state.injection_tick = tick + 1

        return synthetic_snapshots

    def inject_temporal_jitter(
        self,
        baseline_snapshot: TemporalSnapshot,
        magnitude: float = 0.3,
        duration_ticks: int = 10
    ) -> list[TemporalSnapshot]:
        """
        Inject temporal jitter (variance spikes) into Temporal Ledger.

        Creates synthetic snapshots with elevated variance:
        - temporal_variance spiked
        - prediction_error increased
        - convergence_score reduced (smoothing stress)

        Args:
            baseline_snapshot: Baseline temporal snapshot
            magnitude: Jitter magnitude [0.0, 1.0] (0.3 = +30% variance)
            duration_ticks: Number of ticks to sustain jitter

        Returns:
            list[TemporalSnapshot]: Synthetic snapshots for injection
        """
        if not self.is_enabled():
            return []

        self._stress_state.mode = "jitter"
        self._stress_state.injection_active = True
        self._stress_state.magnitude = magnitude

        synthetic_snapshots = []
        for tick in range(duration_ticks):
            # Spike variance/jitter
            snapshot = TemporalSnapshot(
                timestamp=time.time() + tick,
                tri_coherence=baseline_snapshot.tri_coherence,
                tri_drift_z=baseline_snapshot.tri_drift_z,
                slot07_mode=baseline_snapshot.slot07_mode,
                gate_state=baseline_snapshot.gate_state,
                governance_state=baseline_snapshot.governance_state,
                prediction_error=baseline_snapshot.prediction_error + magnitude,
                temporal_drift=baseline_snapshot.temporal_drift,
                temporal_variance=baseline_snapshot.temporal_variance + magnitude,
                convergence_score=max(0.0, baseline_snapshot.convergence_score - magnitude * 0.5),
                divergence_penalty=baseline_snapshot.divergence_penalty + magnitude * 0.3
            )
            synthetic_snapshots.append(snapshot)
            self._stress_state.injection_tick = tick + 1

        return synthetic_snapshots

    def inject_combined_stress(
        self,
        baseline_snapshot: TemporalSnapshot,
        magnitude: float = 0.25,
        duration_ticks: int = 15
    ) -> list[TemporalSnapshot]:
        """
        Inject combined drift + jitter stress (escalation cascade).

        Simulates compound destabilization event:
        - Phase 1 (0-5 ticks): Drift escalation
        - Phase 2 (5-10 ticks): Jitter spikes
        - Phase 3 (10-15 ticks): Combined stress

        Args:
            baseline_snapshot: Baseline temporal snapshot
            magnitude: Combined magnitude [0.0, 1.0]
            duration_ticks: Total duration (recommended: ≥15 ticks)

        Returns:
            list[TemporalSnapshot]: Synthetic snapshots for injection
        """
        if not self.is_enabled():
            return []

        self._stress_state.mode = "combined"
        self._stress_state.injection_active = True
        self._stress_state.magnitude = magnitude

        synthetic_snapshots = []
        phase1_ticks = duration_ticks // 3
        phase2_ticks = duration_ticks // 3
        phase3_ticks = duration_ticks - phase1_ticks - phase2_ticks

        # Phase 1: Drift
        for tick in range(phase1_ticks):
            snapshot = TemporalSnapshot(
                timestamp=time.time() + tick,
                tri_coherence=max(0.0, baseline_snapshot.tri_coherence - magnitude * 0.3),
                tri_drift_z=baseline_snapshot.tri_drift_z + magnitude,
                slot07_mode=baseline_snapshot.slot07_mode,
                gate_state=baseline_snapshot.gate_state,
                governance_state=baseline_snapshot.governance_state,
                prediction_error=baseline_snapshot.prediction_error + magnitude * 0.3,
                temporal_drift=baseline_snapshot.temporal_drift + magnitude,
                temporal_variance=baseline_snapshot.temporal_variance,
                convergence_score=max(0.0, baseline_snapshot.convergence_score - magnitude * 0.3),
                divergence_penalty=baseline_snapshot.divergence_penalty + magnitude * 0.5
            )
            synthetic_snapshots.append(snapshot)

        # Phase 2: Jitter
        for tick in range(phase2_ticks):
            snapshot = TemporalSnapshot(
                timestamp=time.time() + phase1_ticks + tick,
                tri_coherence=max(0.0, baseline_snapshot.tri_coherence - magnitude * 0.2),
                tri_drift_z=baseline_snapshot.tri_drift_z + magnitude * 0.5,
                slot07_mode=baseline_snapshot.slot07_mode,
                gate_state=baseline_snapshot.gate_state,
                governance_state=baseline_snapshot.governance_state,
                prediction_error=baseline_snapshot.prediction_error + magnitude,
                temporal_drift=baseline_snapshot.temporal_drift + magnitude * 0.5,
                temporal_variance=baseline_snapshot.temporal_variance + magnitude,
                convergence_score=max(0.0, baseline_snapshot.convergence_score - magnitude * 0.6),
                divergence_penalty=baseline_snapshot.divergence_penalty + magnitude * 0.7
            )
            synthetic_snapshots.append(snapshot)

        # Phase 3: Combined
        for tick in range(phase3_ticks):
            snapshot = TemporalSnapshot(
                timestamp=time.time() + phase1_ticks + phase2_ticks + tick,
                tri_coherence=max(0.0, baseline_snapshot.tri_coherence - magnitude * 0.4),
                tri_drift_z=baseline_snapshot.tri_drift_z + magnitude * 1.2,
                slot07_mode=baseline_snapshot.slot07_mode,
                gate_state=baseline_snapshot.gate_state,
                governance_state=baseline_snapshot.governance_state,
                prediction_error=baseline_snapshot.prediction_error + magnitude * 1.5,
                temporal_drift=baseline_snapshot.temporal_drift + magnitude * 1.2,
                temporal_variance=baseline_snapshot.temporal_variance + magnitude * 1.3,
                convergence_score=max(0.0, baseline_snapshot.convergence_score - magnitude * 0.8),
                divergence_penalty=baseline_snapshot.divergence_penalty + magnitude
            )
            synthetic_snapshots.append(snapshot)
            self._stress_state.injection_tick = len(synthetic_snapshots)

        return synthetic_snapshots

    def stop_injection(self) -> None:
        """Stop active stress injection and begin recovery phase."""
        self._stress_state.injection_active = False
        self._stress_state.injection_tick = 0

    def record_baseline(self, ris: float, memory_stability: float) -> None:
        """Record baseline RIS and memory stability before stress."""
        self._baseline_ris = ris
        self._baseline_stability = memory_stability
        self._min_ris = ris
        self._min_stability = memory_stability

    def update_metrics(self, ris: float, memory_stability: float, collapse_risk: float) -> None:
        """Update stress state metrics during injection/recovery."""
        self._stress_state.ris = ris
        self._stress_state.memory_stability = memory_stability
        self._stress_state.collapse_risk = collapse_risk
        self._stress_state.timestamp = time.time()

        # Track minimums
        self._min_ris = min(self._min_ris, ris)
        self._min_stability = min(self._min_stability, memory_stability)

        # Record recovery samples
        if not self._stress_state.injection_active:
            self._recovery_samples.append((ris, memory_stability))

    def measure_recovery(self, max_ticks: int = 24) -> RecoveryMetrics:
        """
        Measure recovery metrics after stress injection.

        Recovery criteria (RC):
        - RIS ≥ 0.90 within 24h
        - Memory stability ≥ 0.80 within 24h
        - Recovery rate ≥ 0.90 (normalized)

        Args:
            max_ticks: Maximum ticks to wait for recovery (hours)

        Returns:
            RecoveryMetrics: Recovery tracking results
        """
        if not self._recovery_samples or self._baseline_ris is None:
            return RecoveryMetrics(
                baseline_ris=self._baseline_ris or 0.0,
                baseline_stability=self._baseline_stability or 0.0,
                min_ris=self._min_ris,
                min_stability=self._min_stability,
                final_ris=self._stress_state.ris,
                final_stability=self._stress_state.memory_stability,
                recovery_ticks=0,
                recovered=False,
                recovery_rate=0.0
            )

        # Find recovery tick (RIS ≥ 0.90 AND stability ≥ 0.80)
        recovery_tick = None
        for tick, (ris, stability) in enumerate(self._recovery_samples):
            if ris >= 0.90 and stability >= 0.80:
                recovery_tick = tick
                break

        final_ris, final_stability = self._recovery_samples[-1]
        recovered = recovery_tick is not None and recovery_tick <= max_ticks

        # Compute normalized recovery rate
        if self._min_ris < 1.0:
            recovery_rate = min(1.0, (final_ris - self._min_ris) / (1.0 - self._min_ris))
        else:
            recovery_rate = 1.0

        metrics = RecoveryMetrics(
            baseline_ris=self._baseline_ris,
            baseline_stability=self._baseline_stability or 0.0,
            min_ris=self._min_ris,
            min_stability=self._min_stability,
            final_ris=final_ris,
            final_stability=final_stability,
            recovery_ticks=recovery_tick if recovery_tick is not None else max_ticks,
            recovered=recovered,
            recovery_rate=recovery_rate
        )

        # Record Prometheus metrics (Phase 7.0-RC Step 5)
        try:
            from nova.orchestrator.prometheus_metrics import record_stress_recovery
            record_stress_recovery({
                "recovery_rate": recovery_rate,
                "baseline_ris": self._baseline_ris,
                "recovery_time_hours": recovery_tick if recovery_tick is not None else max_ticks,
                "max_deviation": abs(self._baseline_ris - self._min_ris),
                "timestamp": time.time()
            })
        except Exception:  # pragma: no cover
            pass  # Fail silently

        return metrics

    def get_stress_state(self) -> StressState:
        """Get current stress state."""
        return self._stress_state

    def publish_to_mirror(self, ttl: float = 3600.0) -> None:
        """
        Publish stress state to semantic mirror.

        Key: predictive.stress_snapshot
        TTL: 1h (short-lived, test observability only)
        """
        if not mirror_publish or not self.is_enabled():
            return

        try:
            mirror_publish(
                "predictive.stress_snapshot",
                {
                    "mode": self._stress_state.mode,
                    "injection_active": self._stress_state.injection_active,
                    "injection_tick": self._stress_state.injection_tick,
                    "magnitude": self._stress_state.magnitude,
                    "collapse_risk": self._stress_state.collapse_risk,
                    "ris": self._stress_state.ris,
                    "memory_stability": self._stress_state.memory_stability,
                    "timestamp": self._stress_state.timestamp,
                },
                "stress_test",
                ttl=ttl
            )
        except Exception:  # pragma: no cover
            pass  # Fail silently (test observability, not critical)


# Singleton instance for test coordination
_stress_simulator_instance: Optional[StressSimulator] = None


def get_stress_simulator() -> StressSimulator:
    """Get or create singleton stress simulator instance."""
    global _stress_simulator_instance
    if _stress_simulator_instance is None:
        _stress_simulator_instance = StressSimulator()
    return _stress_simulator_instance


def reset_stress_simulator() -> None:
    """Reset stress simulator (for testing)."""
    global _stress_simulator_instance
    _stress_simulator_instance = StressSimulator()
