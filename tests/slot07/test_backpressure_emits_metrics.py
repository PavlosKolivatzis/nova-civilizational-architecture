import re

from prometheus_client import generate_latest

from nova.governor import state as governor_state
from nova.metrics.registry import REGISTRY
from nova.slots.slot07_production_controls.wisdom_backpressure import decide_job_cap


def test_slot7_emits_metrics_on_decision(monkeypatch):
    monkeypatch.setattr(governor_state, "is_frozen", lambda: False)
    cap = decide_job_cap(stability_margin=0.02)
    assert cap == 6  # reduced_jobs default

    metrics = generate_latest(REGISTRY).decode("utf-8")
    assert re.search(r"^nova_slot07_jobs_current\s+6(\.0+)?$", metrics, re.MULTILINE)
    assert re.search(r"^nova_slot07_jobs_reason\s+1(\.0+)?$", metrics, re.MULTILINE)
