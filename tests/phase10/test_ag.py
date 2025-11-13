"""Tests for Autonomy Governor (AG)."""

import pytest
from nova.phase10.ag import BoundaryEvent, AutonomyGovernor


def test_ag_initialization():
    """Verify AG initialization with defaults."""
    ag = AutonomyGovernor()

    assert ag.tri_min == 0.80
    assert ag.eai_target == 0.85
    assert ag.total_decisions == 0


def test_ag_custom_config():
    """Verify AG custom configuration."""
    config = {
        "tri_min": 0.85,
        "eai_target": 0.90,
        "eai_throttle_threshold": 0.80,
    }
    ag = AutonomyGovernor(config=config)

    assert ag.tri_min == 0.85
    assert ag.eai_target == 0.90
    assert ag.eai_throttle_threshold == 0.80


def test_eai_computation_no_decisions():
    """Verify EAI returns 1.0 when no decisions recorded."""
    ag = AutonomyGovernor()
    eai = ag.compute_eai()

    assert eai == 1.0  # Cautious default


def test_eai_computation_with_decisions():
    """Verify EAI computation formula."""
    ag = AutonomyGovernor()

    # Record 8 safe, 2 unsafe decisions
    for _ in range(8):
        ag.record_decision(safe=True)
    for _ in range(2):
        ag.record_decision(safe=False)

    eai = ag.compute_eai()

    # Expected: (8/10) × 1.0 = 0.8
    assert eai == 0.8


def test_eai_computation_with_consensus_quality():
    """Verify EAI incorporates consensus quality."""
    ag = AutonomyGovernor()
    ag.update_metrics(fcq=0.9)

    # Record 10 safe decisions
    for _ in range(10):
        ag.record_decision(safe=True)

    eai = ag.compute_eai()

    # Expected: (10/10) × 0.9 = 0.9
    assert eai == 0.9


def test_boundary_check_proceed():
    """Verify decision proceeds when within bounds."""
    ag = AutonomyGovernor()
    ag.update_metrics(tri=0.85, csi=0.80)

    # Record sufficient safe decisions to keep EAI high
    for _ in range(10):
        ag.record_decision(safe=True)

    result = ag.check_decision_boundary()

    assert result["action"] == "proceed"
    assert result["requires_human_review"] is False


def test_boundary_check_tri_violation():
    """Verify escalation on TRI violation."""
    ag = AutonomyGovernor()
    ag.update_metrics(tri=0.75)  # Below 0.80 threshold

    result = ag.check_decision_boundary()

    assert result["action"] == "escalate"
    assert result["requires_human_review"] is True
    assert "tri_violation" in result["reason"]
    assert len(ag.escalation_events) == 1


def test_boundary_check_csi_violation():
    """Verify escalation on CSI instability."""
    ag = AutonomyGovernor()
    ag.update_metrics(tri=0.85, csi=0.70)  # CSI below 0.75

    result = ag.check_decision_boundary()

    assert result["action"] == "escalate"
    assert "csi_instability" in result["reason"]


def test_boundary_check_eai_throttle():
    """Verify throttle when EAI drops below threshold."""
    ag = AutonomyGovernor()
    ag.update_metrics(tri=0.85, csi=0.80)

    # Record decisions to bring EAI below 0.75
    for _ in range(5):
        ag.record_decision(safe=True)
    for _ in range(5):
        ag.record_decision(safe=False)  # EAI = 0.5

    result = ag.check_decision_boundary()

    assert result["action"] == "throttle"
    assert result["requires_human_review"] is False
    assert "eai_low" in result["reason"]
    assert len(ag.throttle_events) == 1


def test_decision_recording():
    """Verify decision recording and state updates."""
    ag = AutonomyGovernor()

    ag.record_decision(safe=True, metadata={"decision_id": "d1"})
    ag.record_decision(safe=False, metadata={"decision_id": "d2"})

    assert ag.total_decisions == 2
    assert ag.safe_decisions == 1
    assert len(ag.decision_window) == 2


def test_throttle_rate_computation():
    """Verify throttle rate calculation."""
    ag = AutonomyGovernor()
    ag.update_metrics(tri=0.85, csi=0.80)

    # Trigger 3 throttle events
    for _ in range(3):
        for i in range(5):
            ag.record_decision(safe=False)
        ag.check_decision_boundary()  # Triggers throttle

    # Rate = 3 events / 6 hours = 0.5 events/hour
    rate = ag.get_throttle_rate(window_hours=6)

    assert rate == 0.5


def test_escalation_rate_computation():
    """Verify escalation rate calculation."""
    ag = AutonomyGovernor()

    # Trigger 2 escalation events
    for _ in range(2):
        ag.update_metrics(tri=0.75)  # Violate TRI
        ag.check_decision_boundary()

    rate = ag.get_escalation_rate(window_hours=6)

    # Rate = 2 events / 6 hours ≈ 0.333 events/hour
    assert 0.30 <= rate <= 0.35


def test_ag_metrics_export():
    """Verify metrics export."""
    ag = AutonomyGovernor()
    ag.update_metrics(tri=0.85, csi=0.80, fcq=0.92)

    for _ in range(9):
        ag.record_decision(safe=True)
    ag.record_decision(safe=False)

    metrics = ag.get_metrics()

    assert metrics["eai"] == 0.828  # (9/10) × 0.92
    assert metrics["tri"] == 0.85
    assert metrics["csi"] == 0.80
    assert metrics["fcq"] == 0.92
    assert metrics["total_decisions"] == 10
    assert metrics["safe_decisions"] == 9


def test_boundary_log_export():
    """Verify boundary event log export."""
    ag = AutonomyGovernor()

    # Trigger throttle
    ag.update_metrics(tri=0.85, csi=0.80)
    for _ in range(7):
        ag.record_decision(safe=False)
    ag.check_decision_boundary()

    # Trigger escalation
    ag.update_metrics(tri=0.75)
    ag.check_decision_boundary()

    log = ag.export_boundary_log()

    assert len(log["throttle_events"]) == 1
    assert len(log["escalation_events"]) == 1
    assert log["escalation_events"][0]["reason"].startswith("tri_violation")


def test_ag_within_bounds_metric():
    """Verify within_bounds metric calculation."""
    ag = AutonomyGovernor()
    ag.update_metrics(tri=0.85, csi=0.80, fcq=1.0)

    # Record sufficient safe decisions (EAI = 0.9)
    for _ in range(9):
        ag.record_decision(safe=True)
    ag.record_decision(safe=False)

    metrics = ag.get_metrics()

    assert metrics["within_bounds"] is True  # EAI 0.9 ≥ 0.85, TRI 0.85 ≥ 0.80
