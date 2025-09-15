"""End-to-end rollback test: canary → record promotion → inject breach → rollback → verify."""

from __future__ import annotations
from slots.slot10_civilizational_deployment.core import (
    Slot10Policy, Gatekeeper, CanaryController, SnapshotBackout,
    MockHealthFeed, Slot8Health, Slot4Health, RuntimeMetrics
)


def test_e2e_canary_rollback_coordination():
    """End-to-end test: canary promotes, records snapshots, detects SLO breach, rolls back all slots."""

    # Setup policy with tight rollback timeout for testing
    policy = Slot10Policy(min_stage_duration_s=0, rollback_timeout_s=10.0)

    # Setup health feed and controllers
    health_feed = MockHealthFeed()
    gatekeeper = Gatekeeper(policy, health_feed)
    canary = CanaryController(policy, gatekeeper, health_feed)
    backout = SnapshotBackout(policy)

    # Track restore calls for verification
    restore_calls = {"app": [], "slot8": [], "slot4": []}

    def mock_app_restore(snap_id: str) -> bool:
        restore_calls["app"].append(snap_id)
        return True

    def mock_slot8_restore(snap_id: str) -> bool:
        restore_calls["slot8"].append(snap_id)
        return True

    def mock_slot4_restore(snap_id: str) -> bool:
        restore_calls["slot4"].append(snap_id)
        return True

    # Start canary deployment
    baseline = {"error_rate": 0.01, "latency_p95": 100.0, "saturation": 0.30}
    start_result = canary.start_deployment(baseline)
    assert start_result.action == "start"

    # Record promotion snapshots (simulate taking snapshots before promotion)
    snapshot_set = backout.record_promotion(
        slot10_id="app_v1.2.0",
        slot08_id="mem_snap_abc123",
        slot04_id="tri_model_def456",
        reason="canary_stage_promotion"
    )
    assert snapshot_set.slot10_id == "app_v1.2.0"
    assert snapshot_set.reason == "canary_stage_promotion"

    # Simulate healthy promotion through first stage
    health_result = canary.tick()
    assert health_result.action in ("continue", "promote")

    # INJECT SLO BREACH: Update runtime metrics to exceed error rate threshold
    # Baseline is 0.01, policy multiplier is 1.15, so 0.01 * 1.15 = 0.0115
    # Set current to 0.025 which exceeds threshold
    health_feed.update_runtime(error_rate=0.025)

    # Next tick should detect SLO violation and trigger rollback
    breach_result = canary.tick()
    assert breach_result.action == "rollback"
    assert "SLO violation" in breach_result.reason
    assert "error_rate" in breach_result.reason

    # Execute coordinated cross-slot rollback
    rollback_result = backout.rollback(mock_app_restore, mock_slot8_restore, mock_slot4_restore)

    # Verify rollback succeeded
    assert rollback_result.success is True
    assert rollback_result.slot10_success is True
    assert rollback_result.slot08_success is True
    assert rollback_result.slot04_success is True
    assert rollback_result.execution_time_s <= policy.rollback_timeout_s

    # Verify all restore functions were called with correct snapshot IDs
    assert restore_calls["app"] == ["app_v1.2.0"]
    assert restore_calls["slot8"] == ["mem_snap_abc123"]
    assert restore_calls["slot4"] == ["tri_model_def456"]

    # Verify no MTTR violations
    assert "mttr" not in rollback_result.errors


def test_rollback_with_partial_failure():
    """Test rollback behavior when some slots fail to restore."""

    policy = Slot10Policy(rollback_timeout_s=5.0)
    backout = SnapshotBackout(policy)

    # Record a snapshot set
    backout.record_promotion(
        slot10_id="app_v2.0",
        slot08_id="mem_snap_xyz789",
        slot04_id="tri_model_ghi012"
    )

    # Mock restore functions with slot8 failure
    def app_restore_ok(snap_id: str) -> bool:
        return True

    def slot8_restore_fail(snap_id: str) -> bool:
        return False  # Simulate failure

    def slot4_restore_ok(snap_id: str) -> bool:
        return True

    # Execute rollback
    result = backout.rollback(app_restore_ok, slot8_restore_fail, slot4_restore_ok)

    # Verify partial failure is reported correctly
    assert result.success is False  # Overall failure
    assert result.slot10_success is True
    assert result.slot08_success is False  # Failed
    assert result.slot04_success is True
    assert "slot08" in result.errors
    assert "Failed to restore memory lock" in result.errors["slot08"]


def test_rollback_mttr_validation():
    """Test MTTR violation detection during rollback."""

    import time

    policy = Slot10Policy(rollback_timeout_s=0.1)  # Very tight timeout
    backout = SnapshotBackout(policy)

    backout.record_promotion(slot10_id="app", slot08_id="mem", slot04_id="tri")

    def slow_restore(snap_id: str) -> bool:
        time.sleep(0.2)  # Exceed timeout
        return True

    result = backout.rollback(slow_restore, slow_restore, slow_restore)

    # Should succeed but with MTTR violation
    assert result.success is True  # All restores worked
    assert result.execution_time_s > policy.rollback_timeout_s
    assert "mttr" in result.errors
    assert "0.1s timeout" in result.errors["mttr"]