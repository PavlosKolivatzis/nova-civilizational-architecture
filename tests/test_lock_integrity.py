import pytest

from orchestrator.lock import Lock


def test_lock_verify_integrity_passes():
    lock = Lock.from_anchor("core")
    assert lock.verify_integrity()


def test_lock_verify_integrity_detects_tamper():
    lock = Lock.from_anchor("core")
    lock.integrity_hash = "0" * len(lock.integrity_hash)
    assert not lock.verify_integrity()
    lock = Lock.from_anchor("core")
    lock.anchor = "other"
    assert not lock.verify_integrity()
