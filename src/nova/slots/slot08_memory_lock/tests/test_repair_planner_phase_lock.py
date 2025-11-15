"""Test phase_lock integration in repair planning."""

from nova.slots.slot08_memory_lock.core.repair_planner import RepairPlanner
from nova.slots.slot08_memory_lock.core.types import RepairAction, HealthMetrics, SnapshotMeta


def mk_planner(monkeypatch, phase_lock):
    """Create test planner with phase_lock configuration."""
    monkeypatch.setenv("NOVA_LIGHTCLOCK_DEEP", "1")
    if phase_lock is not None:
        monkeypatch.setenv("SLOT07_PHASE_LOCK", str(phase_lock))
    p = RepairPlanner()
    # Bias history so all actions start similar
    p.success_rates = {
        RepairAction.RESTORE_LAST_GOOD: 0.7,
        RepairAction.SEMANTIC_PATCH: 0.7,
        RepairAction.BLOCK: 0.7
    }
    return p


def test_low_phase_lock_prefers_conservative(monkeypatch):
    """Test that low phase_lock prefers conservative repair strategies."""
    p = mk_planner(monkeypatch, 0.3)

    # Create minimal valid health metrics and snapshots
    hm = HealthMetrics(
        integrity_score=0.5,
        corruption_detected=True,
        tamper_evidence=False,
        checksum_mismatch=True,
        semantic_inversion=False,
        entropy_score=0.3,
        last_snapshot_age_s=300.0,
        repair_attempts=1,
        quarantine_active=False
    )
    snaps = [SnapshotMeta("s1", None, 1000, "merkle123", "signer1", "signature123")]

    dec = p.decide_repair_strategy(hm, snaps, context={})

    # Expect RESTORE_LAST_GOOD or BLOCK to be favored with low phase_lock
    assert dec.action in {RepairAction.RESTORE_LAST_GOOD, RepairAction.BLOCK}

    # Check for phase_lock annotations in decision details
    annotations = dec.details.get('annotations', {})
    assert annotations.get("phase_lock_adjustment") == "conservative_preference"
    assert annotations.get("phase_lock_value") == 0.3


def test_high_phase_lock_normal_operation(monkeypatch):
    """Test that high phase_lock allows normal repair operation."""
    p = mk_planner(monkeypatch, 0.9)

    hm = HealthMetrics(
        integrity_score=0.7,
        corruption_detected=True,
        tamper_evidence=False,
        checksum_mismatch=True,
        semantic_inversion=False,
        entropy_score=0.3,
        last_snapshot_age_s=300.0,
        repair_attempts=1,
        quarantine_active=False
    )
    snaps = [SnapshotMeta("s1", None, 1000, "merkle123", "signer1", "signature123")]

    dec = p.decide_repair_strategy(hm, snaps, context={})

    # Check for normal operation annotation
    annotations = dec.details.get('annotations', {})
    assert annotations.get("phase_lock_adjustment") == "normal_operation"
    assert annotations.get("phase_lock_value") == 0.9


def test_phase_lock_disabled_by_flag(monkeypatch):
    """Test that NOVA_LIGHTCLOCK_DEEP=0 disables phase_lock consideration."""
    monkeypatch.setenv("NOVA_LIGHTCLOCK_DEEP", "0")
    monkeypatch.setenv("SLOT07_PHASE_LOCK", "0.2")

    p = RepairPlanner()
    hm = HealthMetrics(
        integrity_score=0.6,
        corruption_detected=True,
        tamper_evidence=False,
        checksum_mismatch=True,
        semantic_inversion=False,
        entropy_score=0.3,
        last_snapshot_age_s=300.0,
        repair_attempts=1,
        quarantine_active=False
    )
    snaps = [SnapshotMeta("s1", None, 1000, "merkle123", "signer1", "signature123")]

    dec = p.decide_repair_strategy(hm, snaps, context={})

    # No phase_lock annotations should be present when disabled
    annotations = dec.details.get('annotations', {})
    assert "phase_lock_adjustment" not in annotations
    assert "phase_lock_value" not in annotations
