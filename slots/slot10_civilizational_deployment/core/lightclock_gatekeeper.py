from __future__ import annotations
import os
from dataclasses import dataclass
from typing import List, Optional, Set

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

    def evaluate_deploy_gate(self, slot08: dict, slot04: dict) -> LightClockGateResult:
        # Get signals
        tri_score = slot04.get("tri_score")
        if tri_score is None:
            # optional: try mirror if you publish there
            tri_score = self._mirror.read("slot04.tri_score", None)

        phase_lock = self._mirror.read("slot07.phase_lock", None)
        slot9_policy = self._mirror.read("slot09.final_policy", None)

        failed: list[str] = []

        if tri_score is None or tri_score < self._tri_gate:
            failed.append(f"TRI<{self._tri_gate}")

        if phase_lock is None or phase_lock < self._phase_gate:
            failed.append(f"phase_lock<{self._phase_gate}")

        if slot9_policy is None or slot9_policy not in self._allowed_policies:
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