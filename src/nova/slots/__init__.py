"""Nova slot namespace."""

from __future__ import annotations

import logging

memory_logger = logging.getLogger("memory")

# Expose slot registry helpers to callers.
from . import registry  # noqa: E402,F401
