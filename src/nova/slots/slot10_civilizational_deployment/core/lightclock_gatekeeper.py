from __future__ import annotations
import os
from dataclasses import dataclass
from typing import List, Optional, Set

# Real semantic mirror integration (optional)
try:
    from orchestrator.semantic_mirror import get_semantic_mirror
    from orchestrator.mirror_utils import mirror_get
    _global_mirror = get_semantic_mirror()
except Exception:
    _global_mirror = None
    mirror_get = None

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
    slot9_policy: Optional[str] = None
    coherence_level: str = "unknown"
    # friendly flags/reasons
    lightclock_passes: bool = False
    lightclock_reason: str = ""

class LightClockGatekeeper:
    """Checks Light-Clock deploy preconditions: TRI, phase_lock, Slot9 policy."""

    def __init__(self, mirror: MirrorReader | None = None):
        self._mirror = mirror or MirrorReader()
        # thresholds (env-tunable)
        self._tri_gate = float(os.getenv("NOVA_TRI_GATE", "0.66"))
        self._phase_gate = float(os.getenv("NOVA_PHASE_LOCK_GATE", "0.70"))
        self._allowed_policies: Set[str] = set(
            os.getenv("NOVA_SLOT9_ALLOWED", "ALLOW_FASTPATH,STANDARD_PROCESSING").split(",")
        )
        # Circuit breaker to prevent recursive calls
        self._reading_signals = False

    def _read_epistemic_signals(self):
        """Read TRI, phase-lock, and pressure signals with new + legacy key support."""
        # Circuit breaker: prevent recursive calls
        if self._reading_signals:
            return 0.7, 0.5, None, 0.0  # Safe defaults

        self._reading_signals = True
        try:
            coherence = None
            phase_lock = None
            pressure = 0.0
            jitter = None

            # Try local mirror first (backward compatibility)
            if hasattr(self._mirror, "read"):
                phase_lock = self._mirror.read("slot07.phase_lock", None)  # Legacy key
                if phase_lock is None:
                    phase_lock = self._mirror.read("slot03.phase_lock", None)  # New key
                coherence = self._mirror.read("slot04.tri_score", None)  # Legacy key
                if coherence is None:
                    coherence = self._mirror.read("slot04.coherence", None)  # New key
                jitter = self._mirror.read("slot04.phase_jitter", None)
                pressure = self._mirror.read("slot07.pressure_level", 0.0) or 0.0

            # Global mirror fallback (for new integrations)
            if (coherence is None or phase_lock is None) and _global_mirror and mirror_get:
                if phase_lock is None:
                    phase_lock = mirror_get(_global_mirror, "slot03.phase_lock", default=None, requester="slot10_deploy")
                if coherence is None:
                    coherence = mirror_get(_global_mirror, "slot04.coherence", default=None, requester="slot10_deploy")
                if jitter is None:
                    jitter = mirror_get(_global_mirror, "slot04.phase_jitter", default=None, requester="slot10_deploy")
                if pressure == 0.0:
                    pressure = mirror_get(_global_mirror, "slot07.pressure_level", default=0.0, requester="slot10_deploy") or 0.0

            # TRI adapter fallback
            if coherence is None:
                try:
                    from orchestrator.adapters.slot4_tri import Slot4TRIAdapter
                    rep = (Slot4TRIAdapter().get_latest_report() or {})
                    coherence = rep.get("coherence", 0.7)
                    if jitter is None:
                        jitter = rep.get("phase_jitter", None)
                except Exception:
                    coherence = 0.7

            if phase_lock is None:
                phase_lock = 0.5

            return float(coherence), float(phase_lock), (float(jitter) if jitter is not None else None), float(pressure)
        finally:
            self._reading_signals = False

    def should_open_gate(self) -> bool:
        """Check if deployment gate should open based on epistemic signals."""
        coh, pl, jit, p = self._read_epistemic_signals()

        # Tighten threshold under jitter/pressure
        base = self._tri_gate
        if jit is not None and jit >= 0.25:
            base += 0.05
        base += 0.05 * max(0.0, min(1.0, p))

        return coh >= base and 0.45 <= pl <= 0.60

    def evaluate_deploy_gate(self, slot08: dict, slot04: dict) -> LightClockGateResult:
        # Get signals with backward compatibility - NO RECURSIVE CALLS
        tri_score = slot04.get("tri_score")
        if tri_score is None:
            # Try local mirror
            tri_score = self._mirror.read("slot04.tri_score", None)
            if tri_score is None:
                # Direct fallback - avoid recursive call to _read_epistemic_signals
                tri_score = 0.7  # Conservative default

        phase_lock = self._mirror.read("slot07.phase_lock", None)
        if phase_lock is None:
            # Try new key
            phase_lock = self._mirror.read("slot03.phase_lock", None)
            if phase_lock is None:
                # Direct fallback - avoid recursive call to _read_epistemic_signals
                phase_lock = 0.5  # Conservative default

        slot9_policy = self._mirror.read("slot09.final_policy", None)

        failed: list[str] = []

        if tri_score is None or tri_score < self._tri_gate:
            failed.append(f"TRI<{self._tri_gate}")

        if phase_lock is None or phase_lock < self._phase_gate:
            failed.append(f"phase_lock<{self._phase_gate}")

        if slot9_policy is not None and slot9_policy not in self._allowed_policies:
            failed.append(f"slot9_policy_not_allowed({slot9_policy})")

        coherence_level = (
            "high" if (phase_lock is not None and phase_lock >= 0.85)
            else "low" if (phase_lock is not None and phase_lock < 0.4)
            else "medium" if phase_lock is not None
            else "unknown"
        )

        passed = len(failed) == 0
        return LightClockGateResult(
            passed=passed,
            failed_conditions=failed,
            phase_lock_value=phase_lock,
            tri_score=tri_score,
            slot9_policy=slot9_policy,
            coherence_level=coherence_level,
            lightclock_passes=passed,
            lightclock_reason="ok" if passed else ";".join(failed),
        )
