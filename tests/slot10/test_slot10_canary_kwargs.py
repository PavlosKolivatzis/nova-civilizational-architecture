"""Test canary kwargs compatibility for CanaryController."""
from pathlib import Path
import tempfile
from nova.slots.slot10_civilizational_deployment.core.audit import AuditLog


def test_record_accepts_canary_kwargs():
    """Test that AuditLog.record accepts canary pct_from/pct_to kwargs."""
    with tempfile.TemporaryDirectory() as tmp:
        log = AuditLog(Path(tmp))
        rec = log.record(
            action="deploy",
            stage_idx=1,
            reason="canary-step",
            pct_from=10,
            pct_to=25,
            foo="bar",  # future-proof: goes into record.extra
        )
        assert rec.pct_from == 10
        assert rec.pct_to == 25
        assert isinstance(rec.extra, dict) and rec.extra.get("foo") == "bar"


def test_record_without_canary_kwargs():
    """Test that record works without canary kwargs (backward compatibility)."""
    with tempfile.TemporaryDirectory() as tmp:
        log = AuditLog(Path(tmp))
        rec = log.record(
            action="deploy",
            stage_idx=1,
            reason="regular-deploy"
        )
        assert rec.pct_from is None
        assert rec.pct_to is None
        assert rec.extra == {}


def test_canary_data_in_hash_chain():
    """Test that canary data is included in the hashed body."""
    with tempfile.TemporaryDirectory() as tmp:
        log = AuditLog(Path(tmp))

        # Record with canary data
        rec1 = log.record(
            action="canary_start",
            stage_idx=1,
            reason="begin-rollout",
            pct_from=0,
            pct_to=10
        )

        # Record without canary data
        rec2 = log.record(
            action="canary_continue",
            stage_idx=2,
            reason="continue-rollout"
        )

        # Different hashes due to different content
        assert rec1.hash != rec2.hash
        # Chain linking works
        assert rec2.prev == rec1.hash