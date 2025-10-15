"""Shared warning helper for legacy slots shims."""

from __future__ import annotations

import logging
from threading import Lock

_logger = logging.getLogger("slots.shim")
_warned: set[str] = set()
_lock = Lock()

def warn_shim_use(name: str) -> None:
    """Emit a one-time warning when a legacy shim is imported."""
    with _lock:
        if name in _warned:
            return
        _warned.add(name)
    _logger.warning(
        "Importing legacy shim 'slots.%s'; prefer 'nova.slots.%s'.",
        name,
        name,
    )
