import hashlib

from orchestrator.lock import RealityLock


def test_lock_verify_integrity_passes():
    lock = RealityLock.from_anchor("core")
    assert lock.verify_integrity()


def test_lock_verify_integrity_detects_tamper():
    lock = RealityLock.from_anchor("core")
    lock.integrity_hash = "0" * len(lock.integrity_hash)
    assert not lock.verify_integrity()
    lock = RealityLock.from_anchor("core")
    lock.anchor = "other"
    assert not lock.verify_integrity()


def test_from_anchor_generates_sha256_signature():
    lock = RealityLock.from_anchor("core")
    expected = hashlib.sha256(b"core").hexdigest()
    assert lock.integrity_hash == expected
