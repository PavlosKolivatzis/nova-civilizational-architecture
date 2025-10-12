"""Focused tests for Slot 10 MLS audit with shared hash integration."""
import os
import pytest
from pathlib import Path
import tempfile

from nova.slots.slot10_civilizational_deployment.core.audit import AuditLog, _env_truthy


class _DummySigner:
    def sign(self, payload: bytes) -> str:
        return "dummy:" + str(len(payload))


def test_fallback_sha256_when_flag_off(monkeypatch):
    """Test that audit records use SHA256 fallback when shared hash flag is off."""
    monkeypatch.setenv("NOVA_USE_SHARED_HASH", "0")

    with tempfile.TemporaryDirectory() as tmpdir:
        audit_log = AuditLog(Path(tmpdir), signer=_DummySigner())

        record = audit_log.record(
            action="deploy",
            stage_idx=1,
            reason="test_deployment",
            metrics={"a": 1},
            gate={"g": True}
        )

        assert record.hash_method == "fallback_sha256"
        assert record.api_version == "3.1.0-slot10"
        assert record.hash and isinstance(record.hash, str)
        assert record.sig.startswith("dummy:")


def test_env_truthy_variants():
    """Test that _env_truthy handles various truthy values."""
    # Test directly with environment variable
    os.environ["TEST_FLAG"] = "1"
    assert _env_truthy("TEST_FLAG") is True

    os.environ["TEST_FLAG"] = "true"
    assert _env_truthy("TEST_FLAG") is True

    os.environ["TEST_FLAG"] = "YES"
    assert _env_truthy("TEST_FLAG") is True

    os.environ["TEST_FLAG"] = "on"
    assert _env_truthy("TEST_FLAG") is True

    os.environ["TEST_FLAG"] = "0"
    assert _env_truthy("TEST_FLAG") is False

    os.environ["TEST_FLAG"] = "false"
    assert _env_truthy("TEST_FLAG") is False

    os.environ["TEST_FLAG"] = ""
    assert _env_truthy("TEST_FLAG") is False

    # Clean up
    del os.environ["TEST_FLAG"]


def test_shared_blake2b_when_flag_on_and_available(monkeypatch):
    """Test that audit records use blake2b when shared hash is enabled and available."""
    monkeypatch.setenv("NOVA_USE_SHARED_HASH", "true")

    # Import at runtime to check availability
    try:
        shared_available = True
    except Exception:
        shared_available = False

    if not shared_available:
        pytest.skip("Shared hash utility not available")

    with tempfile.TemporaryDirectory() as tmpdir:
        audit_log = AuditLog(Path(tmpdir), signer=_DummySigner())

        # First record
        record1 = audit_log.record(
            action="deploy",
            stage_idx=1,
            reason="first_deployment",
            metrics={"n": 1},
            gate={}
        )

        assert record1.hash_method == "shared_blake2b"
        assert record1.hash and isinstance(record1.hash, str)
        assert record1.api_version == "3.1.0-slot10"

        # Second record - test chain linking
        record2 = audit_log.record(
            action="promote",
            stage_idx=2,
            reason="second_deployment",
            metrics={"n": 2},
            gate={}
        )

        assert record2.hash_method == "shared_blake2b"
        assert record2.prev == record1.hash  # Chain link
        assert record2.hash != record1.hash  # Different hashes


def test_audit_chain_linking():
    """Test that audit records properly chain together."""
    with tempfile.TemporaryDirectory() as tmpdir:
        audit_log = AuditLog(Path(tmpdir), signer=_DummySigner())

        # First record should have empty prev
        record1 = audit_log.record(
            action="start",
            stage_idx=0,
            reason="initial",
            metrics={"start": True}
        )
        assert record1.prev == ""

        # Second record should reference first
        record2 = audit_log.record(
            action="deploy",
            stage_idx=1,
            reason="deployment",
            metrics={"deploy": True}
        )
        assert record2.prev == record1.hash

        # Third record should reference second
        record3 = audit_log.record(
            action="complete",
            stage_idx=2,
            reason="completion",
            metrics={"complete": True}
        )
        assert record3.prev == record2.hash


def test_audit_record_metadata_consistency():
    """Test that audit records have consistent metadata fields."""
    with tempfile.TemporaryDirectory() as tmpdir:
        audit_log = AuditLog(Path(tmpdir), signer=_DummySigner())

        record = audit_log.record(
            action="test",
            stage_idx=1,
            reason="metadata_test",
            metrics={"test": True},
            gate={"enabled": True}
        )

        # Check all required fields are present
        assert hasattr(record, 'hash_method')
        assert hasattr(record, 'api_version')
        assert record.api_version == "3.1.0-slot10"
        assert record.hash_method in ["shared_blake2b", "fallback_sha256"]
        assert record.action == "test"
        assert record.stage_idx == 1
        assert record.reason == "metadata_test"