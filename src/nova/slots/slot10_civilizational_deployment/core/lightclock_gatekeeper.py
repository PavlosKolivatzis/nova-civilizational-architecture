from __future__ import annotations
import os
from dataclasses import dataclass
from typing import Dict, List, Optional, Set

# Real semantic mirror integration (optional)
try:
    from nova.orchestrator.semantic_mirror import get_semantic_mirror
    from nova.orchestrator.mirror_utils import mirror_get
    _global_mirror = get_semantic_mirror()
except Exception:
    _global_mirror = None
    mirror_get = None

try:
    from nova.orchestrator.thresholds.manager import snapshot_thresholds
except Exception:  # pragma: no cover - fallback if orchestrator context absent
    snapshot_thresholds = None

# Minimal interface to read signals; you can swap for your real adapters
class MirrorReader:
    def read(self, key: str, default=None):
        return default

@dataclass
class LightClockGateResult:
    passed: bool
    failed_conditions: List[str]
    # context for metrics
    phase_lock_value: Optional[float] = None
    tri_score: Optional[float] = None
    tri_drift_z: Optional[float] = None
    tri_jitter: Optional[float] = None
    slot9_policy: Optional[str] = None
    coherence_level: str = "unknown"
    # friendly flags/reasons
    lightclock_passes: bool = False
    lightclock_reason: str = ""
    thresholds: Optional[Dict[str, float]] = None

class LightClockGatekeeper:
    """Checks Light-Clock deploy preconditions: TRI, phase_lock, Slot9 policy."""

    def __init__(self, mirror: MirrorReader | None = None):
        self._mirror = mirror or MirrorReader()
        # thresholds (env-tunable)
        self._tri_gate = float(os.getenv("NOVA_TRI_GATE", "0.66"))
        self._phase_gate = float(os.getenv("NOVA_PHASE_LOCK_GATE", "0.70"))
        self._phase_min = float(os.getenv("NOVA_PHASE_LOCK_MIN", "0.45"))
        self._phase_max = float(os.getenv("NOVA_PHASE_LOCK_MAX", "0.60"))
        allowed = os.getenv("NOVA_SLOT9_ALLOWED", "ALLOW_FASTPATH,STANDARD_PROCESSING")
        self._allowed_policies: Set[str] = set(filter(None, (p.strip() for p in allowed.split(","))))
        # Circuit breaker to prevent recursive calls
        self._reading_signals = False

    def _current_thresholds(self) -> Dict[str, float]:
        if snapshot_thresholds is None:
            return {
                "tri_min_coherence": 0.65,
                "slot07_tri_drift_threshold": 2.2,
                "tri_max_jitter": 0.30,
                "slot07_stability_threshold_tri": 0.05,
            }
        try:
            return snapshot_thresholds()
        except Exception:
            return {
                "tri_min_coherence": 0.65,
                "slot07_tri_drift_threshold": 2.2,
                "tri_max_jitter": 0.30,
                "slot07_stability_threshold_tri": 0.05,
            }

    def _read_epistemic_signals(self):
        """Read TRI, phase-lock, and pressure signals with new + legacy key support."""
        # Circuit breaker: prevent recursive calls
        if self._reading_signals:
            return 0.7, 0.5, None, 0.0, None  # Safe defaults

        self._reading_signals = True
        try:
            coherence = None
            phase_lock = None
            pressure = 0.0
            jitter = None
            tri_drift = None

            # Try local mirror first (backward compatibility)
            if hasattr(self._mirror, "read"):
                phase_lock = self._mirror.read("slot07.phase_lock", None)
                if phase_lock is None:
                    phase_lock = self._mirror.read("slot03.phase_lock", None)
                tri_payload = self._mirror.read("slot04.tri_truth_signal", None)
                if isinstance(tri_payload, dict):
                    coherence = tri_payload.get("tri_coherence")
                    tri_drift = tri_payload.get("tri_drift_z")
                    jitter = tri_payload.get("tri_jitter", jitter)
                if coherence is None:
                    coherence = self._mirror.read("slot04.tri_score", None)
                if coherence is None:
                    coherence = self._mirror.read("slot04.coherence", None)
                jitter = self._mirror.read("slot04.phase_jitter", jitter)
                pressure = self._mirror.read("slot07.pressure_level", 0.0) or 0.0

            # Global mirror fallback (for new integrations)
            if (coherence is None or phase_lock is None) and _global_mirror and mirror_get:
                if phase_lock is None:
                    phase_lock = mirror_get(_global_mirror, "slot03.phase_lock", default=None, requester="slot10_deploy")
                if coherence is None:
                    coherence = mirror_get(_global_mirror, "slot04.coherence", default=None, requester="slot10_deploy")
                if jitter is None:
                    jitter = mirror_get(_global_mirror, "slot04.phase_jitter", default=None, requester="slot10_deploy")
                if tri_drift is None:
                    tri_bundle = mirror_get(_global_mirror, "slot04.tri_truth_signal", default=None, requester="slot10_deploy")
                    if isinstance(tri_bundle, dict):
                        tri_drift = tri_bundle.get("tri_drift_z")
                        if coherence is None:
                            coherence = tri_bundle.get("tri_coherence")
                        if jitter is None:
                            jitter = tri_bundle.get("tri_jitter")
                if pressure == 0.0:
                    pressure = mirror_get(_global_mirror, "slot07.pressure_level", default=0.0, requester="slot10_deploy") or 0.0

            # TRI adapter fallback
            if coherence is None:
                try:
                    from nova.orchestrator.adapters.slot4_tri import Slot4TRIAdapter
                    rep = (Slot4TRIAdapter().get_latest_report() or {})
                    coherence = rep.get("coherence", 0.7)
                    if jitter is None:
                        jitter = rep.get("phase_jitter", None)
                    if tri_drift is None:
                        tri_drift = rep.get("tri_drift_z")
                except Exception:
                    coherence = 0.7

            if phase_lock is None:
                phase_lock = 0.5

            return (
                float(coherence),
                float(phase_lock),
                (float(jitter) if jitter is not None else None),
                float(pressure),
                (float(tri_drift) if tri_drift is not None else None),
            )
        finally:
            self._reading_signals = False

    def should_open_gate(self) -> bool:
        """Check if deployment gate should open based on epistemic signals."""
        result = self._evaluate_gate({}, use_window=True)
        return result.passed

    def evaluate_deploy_gate(self, slot08: dict, slot04: dict) -> LightClockGateResult:
        overrides = {
            "tri_score": slot04.get("tri_coherence") or slot04.get("tri_score"),
            "tri_drift_z": slot04.get("tri_drift_z"),
            "tri_jitter": slot04.get("tri_jitter"),
            "phase_lock": slot08.get("phase_lock"),
            "slot9_policy": slot08.get("slot9_policy"),
        }
        return self._evaluate_gate(overrides, use_window=False)

    def _evaluate_gate(self, overrides: Optional[Dict[str, object]] = None, use_window: bool = False) -> LightClockGateResult:
        thresholds = self._current_thresholds()
        tri_gate = max(
            self._tri_gate,
            thresholds.get("tri_min_coherence", 0.65),
        )
        drift_gate = thresholds.get("slot07_tri_drift_threshold", 2.2)
        jitter_gate = thresholds.get("tri_max_jitter", 0.30)
        stability_gate = thresholds.get("slot07_stability_threshold_tri", 0.05)
        if use_window:
            phase_min = max(self._phase_min, stability_gate)
            phase_max = max(self._phase_max, phase_min + 0.1)
        else:
            phase_min = max(self._phase_gate, stability_gate)
            phase_max = float(os.getenv("NOVA_PHASE_LOCK_CEILING", "1.0"))

        coh, phase_lock, jitter, pressure, drift = self._read_epistemic_signals()
        slot9_policy = self._mirror.read("slot09.final_policy", None)

        if overrides:
            if overrides.get("tri_score") is not None:
                coh = overrides["tri_score"]
            if overrides.get("tri_drift_z") is not None:
                drift = overrides["tri_drift_z"]
            if overrides.get("tri_jitter") is not None:
                jitter = overrides["tri_jitter"]
            if overrides.get("phase_lock") is not None:
                phase_lock = overrides["phase_lock"]
            if overrides.get("slot9_policy") is not None:
                slot9_policy = overrides["slot9_policy"]

        failed: list[str] = []
        tri_gate_dynamic = tri_gate
        if jitter is not None and jitter >= jitter_gate:
            tri_gate_dynamic += 0.05
        if pressure:
            tri_gate_dynamic += 0.05 * max(0.0, min(1.0, pressure))

        if coh is None or coh < tri_gate_dynamic:
            failed.append(f"tri_coherence<{tri_gate_dynamic:.2f}")
        if drift is not None and drift > drift_gate:
            failed.append(f"tri_drift>{drift_gate:.2f}")
        if phase_lock is None or not (phase_min <= phase_lock <= phase_max):
            failed.append(f"phase_lock∉[{phase_min:.2f},{phase_max:.2f}]")
        if slot9_policy is not None and slot9_policy not in self._allowed_policies:
            failed.append(f"slot9_policy_not_allowed({slot9_policy})")

        coherence_level = (
            "high" if (phase_lock is not None and phase_lock >= phase_min + 0.1)
            else "low" if (phase_lock is not None and phase_lock < phase_min)
            else "medium" if phase_lock is not None
            else "unknown"
        )

        passed = len(failed) == 0
        return LightClockGateResult(
            passed=passed,
            failed_conditions=failed,
            phase_lock_value=phase_lock,
            tri_score=coh,
            tri_drift_z=drift,
            tri_jitter=jitter,
            slot9_policy=slot9_policy,
            coherence_level=coherence_level,
            lightclock_passes=passed,
            lightclock_reason="ok" if passed else ";".join(failed),
            thresholds={
                "tri_min_coherence": tri_gate_dynamic,
                "tri_drift_threshold": drift_gate,
                "tri_jitter_threshold": jitter_gate,
                "phase_min": phase_min,
                "phase_max": phase_max,
            },
        )
