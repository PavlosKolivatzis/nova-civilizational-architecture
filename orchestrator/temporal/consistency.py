"""Temporal consistency placeholder."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Any


@dataclass
class TemporalConsistency:
    status: str = "unimplemented"
    data: Dict[str, Any] = None
