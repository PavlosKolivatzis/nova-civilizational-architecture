from slots.slot02_deltathresh.core import DeltaThreshProcessor
from slots.slot02_deltathresh.config import ProcessingConfig, OperationalMode

def test_basic_process_content_runs():
    p = DeltaThreshProcessor(ProcessingConfig())
    r = p.process_content("This is an undeniable truth that everyone knows.")
    assert r.action in {"allow","quarantine","neutralize"}
    assert 0.0 <= r.tri_score <= 1.0
    assert set(r.layer_scores.keys()) == {"delta","sigma","theta","omega"}


def test_pass_through_mode_allows_all():
    p = DeltaThreshProcessor(ProcessingConfig())
    p.reconfigure_operational_mode(OperationalMode.PASS_THROUGH)
    r = p.process_content("Everyone knows this is the truth.")
    assert r.action == "allow"
    # No quarantine metrics should be incremented when pass-through is active
    assert p.performance_tracker.quarantined == 0
    assert p.performance_tracker.allowed == 1
