from __future__ import annotations

from typing import Any, Callable, Dict, Iterable

VerifyAnchor = Callable[[str, Any], bool]


def trigger_recovery(protocol: Any, verify_anchor: VerifyAnchor) -> bool:
    """Verify required locks before recovery.

    Parameters
    ----------
    protocol: Any
        Object providing ``required_locks`` iterable and ``locks`` mapping.
    verify_anchor: Callable[[str, Any], bool]
        Function used to validate each lock's anchor.

    Returns
    -------
    bool
        ``True`` when all required locks are present and verified.

    Raises
    ------
    RuntimeError
        If a required lock is missing or fails verification.
    """
    required: Iterable[str] = getattr(protocol, "required_locks", [])
    locks: Dict[str, Any] = getattr(protocol, "locks", {})
    for domain in required:
        if domain not in locks:
            raise RuntimeError(f"missing required lock: {domain}")
        if not verify_anchor(domain, locks[domain]):
            raise RuntimeError(f"lock verification failed: {domain}")
    return True
