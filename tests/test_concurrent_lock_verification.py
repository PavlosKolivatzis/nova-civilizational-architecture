import time
from threading import Thread

from orchestrator.lock import RealityLock
from orchestrator.reality_verifier import RealityVerifier


class SlowRealityLock(RealityLock):
    """RealityLock with an intentionally slow verification."""

    def verify_integrity(self) -> bool:  # type: ignore[override]
        time.sleep(0.1)
        return super().verify_integrity()


def test_concurrent_verification_reduces_contention():
    lock = SlowRealityLock.from_anchor("core")
    verifier = RealityVerifier(lock)

    def worker():
        assert verifier.verify()["valid"]

    threads = [Thread(target=worker) for _ in range(3)]
    start = time.perf_counter()
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    concurrent = time.perf_counter() - start

    # Sequential baseline
    lock2 = SlowRealityLock.from_anchor("core")
    verifier2 = RealityVerifier(lock2)
    start_seq = time.perf_counter()
    for _ in range(3):
        verifier2.verify()
    sequential = time.perf_counter() - start_seq

    assert concurrent < sequential / 2
    assert verifier.get_metrics()["verifications"] == 3
