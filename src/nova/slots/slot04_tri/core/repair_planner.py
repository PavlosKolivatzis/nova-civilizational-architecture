from __future__ import annotations
from collections import defaultdict
from .types import RepairDecision, Health

class RepairPlanner:
    def __init__(self):
        self._succ = defaultdict(int)
        self._fail = defaultdict(int)
        self.success_rates = defaultdict(lambda: 0.7)

    def decide(self, health: Health, *, last_good_id: str | None) -> RepairDecision:
        if not health.data_ok or not health.perf_ok or health.drift_z >= 3.0:
            if last_good_id:
                return RepairDecision("RESTORE_PREV_MODEL","drift_or_perf_degraded",{"snapshot": last_good_id},0.75,2.0)
            return RepairDecision("SAFE_MODE_BLOCK","no_snapshot_available",{},0.6,0.2)
        return RepairDecision("NOOP","healthy",{},0.8,0.05)

    def record_outcome(self, decision: RepairDecision, success: bool, duration_s: float):
        a = decision.action
        if success:
            self._succ[a] += 1
        else:
            self._fail[a] += 1
        s, f = self._succ[a], self._fail[a]
        # Beta(1,1)
        self.success_rates[a] = (s + 1) / (s + f + 2)