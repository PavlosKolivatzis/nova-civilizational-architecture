from slots.slot02_deltathresh.core import DeltaThreshProcessor
from slots.slot02_deltathresh.config import ProcessingConfig

def test_basic_process_content_runs():
    p = DeltaThreshProcessor(ProcessingConfig())
    r = p.process_content("This is an undeniable truth that everyone knows.")
    assert r.action in {"allow","quarantine","neutralize"}
    assert 0.0 <= r.tri_score <= 1.0
    assert set(r.layer_scores.keys()) == {"delta","sigma","theta","omega"}
