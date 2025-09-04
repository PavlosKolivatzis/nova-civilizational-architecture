from slots.slot02_deltathresh.core import DeltaThreshProcessor
from slots.slot02_deltathresh.config import (
    ProcessingConfig,
    OperationalMode,
    ProcessingMode,
)

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


def test_pass_through_allows_but_reports_reasons():
    p = DeltaThreshProcessor(ProcessingConfig())
    p.config.operational_mode = OperationalMode.PASS_THROUGH
    p.config.quarantine_enabled = False
    action, reasons = p._determine_action(
        tri_score=0.99,
        layer_scores={"delta": 1.0},
        content="x",
    )
    assert action == "allow"
    assert reasons


def test_enforcing_quarantines():
    p = DeltaThreshProcessor(ProcessingConfig())
    p.config.processing_mode = ProcessingMode.QUARANTINE_ONLY
    action, reasons = p._determine_action(
        tri_score=0.99,
        layer_scores={"delta": 1.0},
        content="x",
    )
    assert action == "quarantine"
    assert reasons
